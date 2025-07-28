import threading

from account_manager import create_app
from account_manager.tasks import start_background_tasks
from account_manager.tray import run_tray_icon

app = create_app()


if __name__ == "__main__":
    task_threads = start_background_tasks()

    tray_thread = threading.Thread(target=run_tray_icon, daemon=True)
    tray_thread.start()

    print("Starting Flask server on http://127.0.0.1:5000")
    print("Performance optimizations enabled:")
    print("- Connection pooling with WAL mode")
    print("- Database indexing")
    print("- Batch operations")
    print("- Response caching")
    print("- Optimized background threads")

    app.run(debug=False, threaded=True)