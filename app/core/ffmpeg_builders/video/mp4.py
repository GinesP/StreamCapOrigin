from ..base import FFmpegCommandBuilder


class MP4CommandBuilder(FFmpegCommandBuilder):
    def build_command(self) -> list[str]:
        command = self._get_basic_ffmpeg_command()
        if self.segment_record:
            additional_commands = [
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0",
                "-f", "segment",
                "-segment_time", str(self.segment_time),
                "-segment_format", "mp4",
                "-reset_timestamps", "1",
                "-movflags", "+frag_keyframe+empty_moov",
                "-flags", "global_header",
                self.full_path,
            ]
        else:
            additional_commands = [
                "-map", "0",
                "-c:v", "copy",
                "-c:a", "copy",
                "-f", "mp4",
                self.full_path,
            ]

        command.extend(additional_commands)
        return command
