import traceback
import json
import subprocess
from typing import Optional


# ── 在此处填入 task3 所需的常量 ──────────────────────────────────────────────
# BASE_URL = "..."
# TOKEN = "..."
# ...


# ── 在此处填入 task3 的核心业务逻辑函数 ──────────────────────────────────────


async def run_task3_task(webhook_url: Optional[str] = None):
    print("--- Background task: run_task3_task started ---", flush=True)
    result_payload = {}
    try:
        # ── 在此处填入 task3 的主流程 ────────────────────────────────────────
        # 例如：
        #   data = await some_scrape_function()
        #   result = post_something(data)
        #   result_payload = {"status": "success", "data": result}
        raise NotImplementedError("run_task3_task is not implemented yet.")

    except Exception as e:
        error_message = f"Error: {e}"
        print("--- Background task: run_task3_task encountered an error ---", flush=True)
        print(error_message, flush=True)
        traceback.print_exc()
        result_payload = {"status": "error", "message": error_message, "traceback": traceback.format_exc()}

    finally:
        if webhook_url:
            try:
                print(f"--- Sending callback to webhook via curl: {webhook_url} ---", flush=True)
                json_data = json.dumps(result_payload)
                command = [
                    "curl",
                    "-X", "POST",
                    "-H", "Content-Type: application/json",
                    "-d", json_data,
                    "--max-time", "10",
                    webhook_url,
                ]
                process = subprocess.run(command, capture_output=True, text=True, check=False)
                if process.returncode == 0:
                    print(f"--- curl callback sent successfully. Response: {process.stdout}", flush=True)
                else:
                    print(f"--- FAILED to send webhook callback via curl. Return code: {process.returncode}", flush=True)
                    print(f"--- curl stderr: {process.stderr}", flush=True)
            except Exception as e:
                print(f"--- FAILED to execute curl command: {e} ---", flush=True)
                traceback.print_exc()

        print("--- Background task: run_task3_task finished ---", flush=True)
