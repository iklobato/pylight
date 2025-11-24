"""Main application file for starter todo-app."""

# Note: In generated projects, these will be available from pylight package
# from pylight import LightApi
# from src.models.user import User
# from src.models.project import Project
# from src.models.task import Task

# Placeholder for now - will be replaced during template processing
print("Pylight framework will be installed and imported here")

if __name__ == "__main__":
    app = LightApi(
        database_url="sqlite:///app.db",
        swagger_title="Todo App API",
        swagger_version="1.0.0",
        swagger_description="A starter todo-app demonstrating Pylight features",
    )

    app.register(User)
    app.register(Project)
    app.register(Task)

    app.run(host="localhost", port=8000, debug=True)

