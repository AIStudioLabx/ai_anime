"""角色配音服务"""
import json
import pyttsx3
from pathlib import Path
from typing import Dict, Any, List, Optional
import tempfile
import subprocess


class AudioService:
    """角色配音服务"""

    def __init__(self):
        # services/ -> 项目根目录（使用绝对路径）
        self.project_root = Path(__file__).resolve().parent.parent
        self.config_path = self.project_root / "config" / "voice_config.json"
        self.audio_dir = self.project_root / "assets" / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载声音配置
        self.voice_config = self._load_voice_config()
        
        # 初始化 TTS 引擎
        self.engine = None
        self._init_engine()

    def _load_voice_config(self) -> Dict[str, Any]:
        """加载声音配置文件"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # 返回默认配置
            return {
                "default": {
                    "rate": 150,
                    "volume": 0.9,
                    "voice_name": "Ting-Ting"  # macOS say 命令的声音名称
                },
                "characters": {}
            }

    def _init_engine(self):
        """初始化 TTS 引擎"""
        try:
            # 在 macOS 上，尝试使用 nsss（系统默认）或 say 驱动
            import platform
            if platform.system() == "Darwin":  # macOS
                try:
                    self.engine = pyttsx3.init("nsss")  # macOS 系统 TTS
                except:
                    self.engine = pyttsx3.init()  # 回退到默认
            else:
                self.engine = pyttsx3.init()
            
            # 设置默认参数
            default_config = self.voice_config.get("default", {})
            self.engine.setProperty("rate", default_config.get("rate", 150))
            self.engine.setProperty("volume", default_config.get("volume", 0.9))
        except Exception as e:
            raise RuntimeError(f"无法初始化 TTS 引擎: {e}")

    def _get_voice_config_for_character(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """获取角色的声音配置"""
        # 支持 voice_id 或 voice_name 字段
        voice_id = character.get("voice_id") or character.get("voice_name")
        if voice_id and voice_id in self.voice_config.get("characters", {}):
            return self.voice_config["characters"][voice_id]
        
        # 使用默认配置
        return self.voice_config.get("default", {
            "rate": 150,
            "volume": 0.9,
            "voice_name": "Ting-Ting"
        })

    def _apply_voice_settings(self, config: Dict[str, Any]):
        """应用声音设置到引擎（用于 pyttsx3）"""
        if self.engine is None:
            return
        
        if "rate" in config:
            self.engine.setProperty("rate", config["rate"])
        if "volume" in config:
            self.engine.setProperty("volume", config["volume"])
        
        # 设置声音（优先使用 voice_name，如果没有则尝试 voice_id）
        voice_name = config.get("voice_name")
        if voice_name:
            # 尝试通过名称匹配
            voices = self.engine.getProperty("voices")
            if voices and len(voices) > 0:
                for voice in voices:
                    if voice_name.lower() in voice.name.lower() or voice.name.lower() in voice_name.lower():
                        self.engine.setProperty("voice", voice.id)
                        break
        
        # 兼容旧的 voice_id 配置
        elif config.get("voice_id") is not None:
            voices = self.engine.getProperty("voices")
            if voices and len(voices) > 0:
                voice_id = config["voice_id"]
                if isinstance(voice_id, int) and 0 <= voice_id < len(voices):
                    self.engine.setProperty("voice", voices[voice_id].id)
                elif isinstance(voice_id, str):
                    # 尝试通过名称匹配
                    for voice in voices:
                        if voice_id.lower() in voice.name.lower():
                            self.engine.setProperty("voice", voice.id)
                            break

    def _text_to_speech(self, text: str, output_path: Path, config: Dict[str, Any], target_duration: Optional[float] = None):
        """
        将文本转换为语音并保存到文件
        
        Args:
            text: 要转换的文本
            output_path: 输出文件路径
            config: 声音配置
            target_duration: 目标时长（秒），如果提供则调整音频速度以匹配
        """
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")
        
        import platform
        import time
        
        # 在 macOS 上，直接使用 say 命令更可靠
        if platform.system() == "Darwin":  # macOS
            self._text_to_speech_macos(text, output_path, config)
        else:
            # 其他系统使用 pyttsx3
            self._text_to_speech_pyttsx3(text, output_path, config)
        
        # 如果指定了目标时长，调整音频速度
        if target_duration and target_duration > 0:
            try:
                self._adjust_audio_duration(output_path, target_duration)
            except Exception as e:
                # 如果调整时长失败，记录警告但继续（至少音频已经生成了）
                print(f"警告: 调整音频时长失败: {e}")
                import traceback
                print(traceback.format_exc())
    
    def _text_to_speech_macos(self, text: str, output_path: Path, config: Dict[str, Any]):
        """使用 macOS say 命令生成语音（更可靠）"""
        import subprocess
        import time
        
        # 使用临时 WAV 文件
        with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp_file:
            tmp_aiff = Path(tmp_file.name)
        
        try:
            # 构建 say 命令
            # say -v 声音名称 -r 语速 -o 输出文件 "文本"
            cmd = ["say"]
            
            # 设置声音（优先使用 voice_name，如果没有则尝试从 voice_id 获取）
            voice_name = config.get("voice_name")
            
            if not voice_name and config.get("voice_id") is not None:
                # 尝试从 voice_id 获取声音名称（兼容旧配置）
                try:
                    engine = pyttsx3.init("nsss")
                    voices = engine.getProperty("voices")
                    if voices:
                        voice_id = config["voice_id"]
                        if isinstance(voice_id, int) and 0 <= voice_id < len(voices):
                            voice_name = voices[voice_id].name
                        elif isinstance(voice_id, str):
                            for voice in voices:
                                if voice_id.lower() in voice.name.lower():
                                    voice_name = voice.name
                                    break
                    engine.stop()
                except:
                    pass
            
            if voice_name:
                cmd.extend(["-v", voice_name])
            
            # 设置语速（say 的 -r 参数，默认是 200）
            rate = config.get("rate", 150)
            # 将 pyttsx3 的 rate (150) 转换为 say 的 rate (约 200)
            say_rate = int(rate * 200 / 150)
            cmd.extend(["-r", str(say_rate)])
            
            # 输出文件
            cmd.extend(["-o", str(tmp_aiff)])
            
            # 文本内容
            cmd.append(text)
            
            # 执行 say 命令
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # 等待文件生成
            max_wait = 10
            waited = 0
            while waited < max_wait:
                if tmp_aiff.exists() and tmp_aiff.stat().st_size > 0:
                    break
                time.sleep(0.2)
                waited += 0.2
            
            if not tmp_aiff.exists() or tmp_aiff.stat().st_size == 0:
                raise RuntimeError(f"AIFF 文件生成失败: {tmp_aiff}")
            
            # 转换为 MP3
            if output_path.suffix.lower() == ".mp3":
                self._convert_aiff_to_mp3(tmp_aiff, output_path)
            else:
                # 转换为 WAV
                self._convert_aiff_to_wav(tmp_aiff, output_path)
        finally:
            if tmp_aiff.exists():
                tmp_aiff.unlink()
    
    def _text_to_speech_pyttsx3(self, text: str, output_path: Path, config: Dict[str, Any]):
        """使用 pyttsx3 生成语音（非 macOS 系统）"""
        engine = None
        try:
            engine = pyttsx3.init()
            
            # 应用声音设置
            if "rate" in config:
                engine.setProperty("rate", config["rate"])
            if "volume" in config:
                engine.setProperty("volume", config["volume"])
            
            # 设置声音
            if config.get("voice_id") is not None:
                voices = engine.getProperty("voices")
                if voices and len(voices) > 0:
                    voice_id = config["voice_id"]
                    if isinstance(voice_id, int) and 0 <= voice_id < len(voices):
                        engine.setProperty("voice", voices[voice_id].id)
                    elif isinstance(voice_id, str):
                        for voice in voices:
                            if voice_id.lower() in voice.name.lower():
                                engine.setProperty("voice", voice.id)
                                break
            
            # 使用临时 WAV 文件
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_wav = Path(tmp_file.name)
            
            try:
                engine.save_to_file(text, str(tmp_wav))
                engine.runAndWait()
                
                import time
                time.sleep(0.5)
                
                if not tmp_wav.exists() or tmp_wav.stat().st_size == 0:
                    raise RuntimeError(f"WAV 文件生成失败: {tmp_wav}")
                
                if output_path.suffix.lower() == ".mp3":
                    self._convert_wav_to_mp3(tmp_wav, output_path)
                else:
                    import shutil
                    shutil.copy2(tmp_wav, output_path)
            finally:
                if tmp_wav.exists():
                    tmp_wav.unlink()
        finally:
            if engine is not None:
                try:
                    engine.stop()
                except:
                    pass
    
    def _convert_aiff_to_mp3(self, aiff_path: Path, mp3_path: Path):
        """将 AIFF 转换为 MP3"""
        self._convert_audio_to_mp3(aiff_path, mp3_path)
    
    def _convert_aiff_to_wav(self, aiff_path: Path, wav_path: Path):
        """将 AIFF 转换为 WAV"""
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(aiff_path),
                str(wav_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode() if e.stderr else str(e))
            raise RuntimeError(f"AIFF 转 WAV 失败: {error_msg}")
    
    def _convert_audio_to_mp3(self, audio_path: Path, mp3_path: Path):
        """通用的音频转 MP3 方法"""
        try:
            if not audio_path.exists():
                raise RuntimeError(f"源文件不存在: {audio_path}")
            
            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(audio_path),
                "-codec:a", "libmp3lame",
                "-q:a", "2",
                "-ar", "22050",
                "-ac", "1",
                "-b:a", "64k",
                str(mp3_path)
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            import time
            time.sleep(0.2)
            
            if not mp3_path.exists():
                raise RuntimeError(f"MP3 文件未生成: {mp3_path}")
            
            mp3_size = mp3_path.stat().st_size
            if mp3_size == 0:
                raise RuntimeError(f"MP3 文件为空: {mp3_path}")
            
            if mp3_size < 1024:
                raise RuntimeError(f"MP3 文件太小 ({mp3_size} bytes): {mp3_path}")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode() if e.stderr else str(e))
            raise RuntimeError(f"音频转换失败: {error_msg}")
        except FileNotFoundError:
            raise RuntimeError("ffmpeg 未找到，请确保已安装 ffmpeg")

    def _convert_wav_to_mp3(self, wav_path: Path, mp3_path: Path):
        """使用 ffmpeg 将 WAV 转换为 MP3"""
        self._convert_audio_to_mp3(wav_path, mp3_path)
    
    def _generate_silence(self, duration: float) -> Optional[Path]:
        """
        生成指定时长的静音音频
        
        Args:
            duration: 静音时长（秒）
            
        Returns:
            生成的静音音频文件路径
        """
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            silence_path = Path(tmp_file.name)
        
        try:
            # 使用 ffmpeg 生成静音
            cmd = [
                "ffmpeg",
                "-y",
                "-f", "lavfi",
                "-i", f"anullsrc=channel_layout=mono:sample_rate=22050",
                "-t", str(duration),
                "-codec:a", "libmp3lame",
                "-q:a", "2",
                "-ar", "22050",
                "-ac", "1",
                "-b:a", "64k",
                str(silence_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            if silence_path.exists() and silence_path.stat().st_size > 0:
                return silence_path
            else:
                silence_path.unlink(missing_ok=True)
                return None
        except Exception as e:
            print(f"警告: 生成静音失败: {e}")
            if silence_path.exists():
                silence_path.unlink(missing_ok=True)
            return None
    
    def _concat_audio_segments(self, segments: List[Path], output_path: Path, target_duration: Optional[float] = None):
        """
        将多个音频段拼接成一个音频文件
        
        Args:
            segments: 音频段路径列表
            output_path: 输出文件路径
            target_duration: 目标总时长（秒），如果提供则调整速度
        """
        if not segments:
            raise ValueError("音频段列表不能为空")
        
        # 如果只有一个段，直接复制
        if len(segments) == 1:
            import shutil
            shutil.copy2(segments[0], output_path)
            if target_duration:
                self._adjust_audio_duration(output_path, target_duration)
            return
        
        # 创建文件列表
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            concat_list_path = Path(f.name)
            for seg in segments:
                f.write(f"file '{seg.absolute()}'\n")
        
        try:
            # 使用 ffmpeg concat 拼接
            cmd = [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list_path),
                "-codec:a", "libmp3lame",
                "-q:a", "2",
                "-ar", "22050",
                "-ac", "1",
                "-b:a", "64k",
                str(output_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # 如果指定了目标时长，调整速度
            if target_duration:
                self._adjust_audio_duration(output_path, target_duration)
        finally:
            if concat_list_path.exists():
                concat_list_path.unlink()
    
    def _adjust_audio_duration(self, audio_path: Path, target_duration: float):
        """
        调整音频时长以匹配目标时长
        
        Args:
            audio_path: 音频文件路径
            target_duration: 目标时长（秒）
        """
        import subprocess
        import tempfile
        
        # 获取当前音频时长
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path)
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            current_duration = float(result.stdout.strip())
        except Exception as e:
            print(f"警告: 无法获取音频时长，跳过速度调整: {e}")
            return
        
        # 如果时长已经匹配（误差在 0.1 秒内），不需要调整
        if abs(current_duration - target_duration) < 0.1:
            return
        
        # 计算需要的速度调整比例
        speed_ratio = current_duration / target_duration
        
        # atempo 滤镜的范围是 0.5 到 2.0，如果超出范围需要链式使用
        if speed_ratio < 0.5:
            # 太慢，需要多次应用 atempo
            # 例如：0.25 = 0.5 * 0.5，需要两次
            # 计算需要多少个 atempo 才能达到目标速度
            num_filters = 1
            while (0.5 ** num_filters) > speed_ratio:
                num_filters += 1
            tempo_value = speed_ratio ** (1.0 / num_filters)
            # 确保每个 atempo 值在 0.5-2.0 范围内
            if tempo_value < 0.5:
                num_filters += 1
                tempo_value = speed_ratio ** (1.0 / num_filters)
            filter_complex = ",".join([f"atempo={tempo_value:.3f}"] * num_filters)
        elif speed_ratio > 2.0:
            # 太快，需要多次应用 atempo
            # 计算需要多少个 atempo 才能达到目标速度
            num_filters = 1
            while (2.0 ** num_filters) < speed_ratio:
                num_filters += 1
            tempo_value = speed_ratio ** (1.0 / num_filters)
            # 确保每个 atempo 值在 0.5-2.0 范围内
            if tempo_value > 2.0:
                num_filters += 1
                tempo_value = speed_ratio ** (1.0 / num_filters)
            filter_complex = ",".join([f"atempo={tempo_value:.3f}"] * num_filters)
        else:
            filter_complex = f"atempo={speed_ratio:.3f}"
        
        # 使用临时文件
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_output = Path(tmp_file.name)
        
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(audio_path),
                "-filter:a", filter_complex,
                "-codec:a", "libmp3lame",
                "-q:a", "2",
                str(tmp_output)
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # 替换原文件
            import shutil
            shutil.move(str(tmp_output), str(audio_path))
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode() if e.stderr else str(e))
            print(f"警告: 音频速度调整失败: {error_msg}")
            if tmp_output.exists():
                tmp_output.unlink()
            # 不抛出异常，保留原始音频文件
            return
        except Exception as e:
            print(f"警告: 音频速度调整出错: {e}")
            if tmp_output.exists():
                tmp_output.unlink()
            # 不抛出异常，保留原始音频文件
            return

    def generate_audio(
        self,
        episode_data: Dict[str, Any],
        episode_id: Optional[int] = None,
    ) -> List[Path]:
        """
        为 episode 生成配音音频文件

        Args:
            episode_data: episode JSON 数据
            episode_id: episode ID，如果不提供则从 episode_data 中读取

        Returns:
            生成的音频文件路径列表
        """
        if episode_id is None:
            episode_id = episode_data.get("episode_id", 1)

        character = episode_data.get("character", {})
        voice_config = self._get_voice_config_for_character(character)
        
        audio_files = []
        
        for shot in episode_data.get("shots", []):
            shot_id = shot.get("id", len(audio_files) + 1)
            subtitles = shot.get("subtitles", [])
            shot_duration = shot.get("duration", 0)
            
            if not subtitles:
                continue
            
            # 检查是否有指定的说话者
            speaker = shot.get("speaker")
            if speaker and speaker in self.voice_config.get("characters", {}):
                # 使用指定说话者的声音配置
                shot_voice_config = self.voice_config["characters"][speaker]
            else:
                # 使用角色默认声音配置
                shot_voice_config = voice_config
            
            # 计算每个字幕的时长（与 SRT 生成逻辑保持一致）
            per_line_duration = shot_duration / max(len(subtitles), 1)
            
            # 为每个字幕生成音频段，然后拼接
            audio_segments = []
            for i, subtitle_text in enumerate(subtitles):
                # 检查是否是静音内容（只有省略号、破折号等）
                subtitle_clean = subtitle_text.strip()
                is_silence = (
                    subtitle_clean in ["……", "...", "…", "——", "--", "—", ""] or
                    subtitle_clean.replace("…", "").replace(".", "").replace("—", "").replace("-", "").strip() == ""
                )
                
                if is_silence:
                    # 生成静音音频段
                    segment_duration = per_line_duration * 0.9  # 与 SRT 逻辑保持一致
                    silence_path = self._generate_silence(segment_duration)
                    if silence_path:
                        audio_segments.append(silence_path)
                else:
                    # 生成语音音频段
                    segment_path = self.audio_dir / f"episode_{episode_id:03d}_shot_{shot_id}_seg_{i}.mp3"
                    try:
                        self._text_to_speech(
                            subtitle_text,
                            segment_path,
                            shot_voice_config,
                            target_duration=per_line_duration * 0.9
                        )
                        if segment_path.exists():
                            audio_segments.append(segment_path)
                    except Exception as e:
                        print(f"警告: 为字幕 '{subtitle_text}' 生成音频失败: {e}")
                        # 生成静音作为替代
                        silence_path = self._generate_silence(per_line_duration * 0.9)
                        if silence_path:
                            audio_segments.append(silence_path)
            
            # 如果生成了音频段，拼接成一个完整的音频文件
            if audio_segments:
                audio_filename = f"episode_{episode_id:03d}_shot_{shot_id}.mp3"
                audio_path = self.audio_dir / audio_filename
                
                try:
                    self._concat_audio_segments(audio_segments, audio_path, target_duration=shot_duration)
                    audio_files.append(audio_path)
                except Exception as e:
                    print(f"错误: 拼接音频段失败: {e}")
                    import traceback
                    print(traceback.format_exc())
                
                # 清理临时音频段文件
                for seg in audio_segments:
                    if seg.exists() and seg != audio_path:
                        seg.unlink()
        
        return audio_files

