import asyncio
import os

from .utils.logger import logger


class AsyncProcessManager:
    def __init__(self):
        self.ffmpeg_processes: list[asyncio.subprocess.Process] = []

    def add_process(self, process: asyncio.subprocess.Process):
        """Add an asynchronous process to the management list"""
        self.ffmpeg_processes.append(process)

    async def cleanup(self):
        """Asynchronously clean up all processes"""
        cleanup_tasks = []
        for process in self.ffmpeg_processes:
            if process.returncode is None:
                task = self._terminate_process(process)
                cleanup_tasks.append(task)

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks)

        self.ffmpeg_processes = []

    @staticmethod
    async def _terminate_process(process: asyncio.subprocess.Process):
        """Asynchronously terminate a single process"""
        try:
            # On Windows, send 'q' to stdin to gracefully terminate FFmpeg
            if os.name == 'nt' and process.stdin:
                process.stdin.write(b'q')
                await process.stdin.drain()
                process.stdin.close()
            else:
                process.terminate()

            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

        except Exception as e:
            logger.error(f"Error occurred while terminating process: {str(e)}")
