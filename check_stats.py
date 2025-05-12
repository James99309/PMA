from app import create_app
from app.models.projectpm_statistics import ProjectStatistics
app = create_app()
with app.app_context():
    stats = ProjectStatistics.get_project_statistics()
