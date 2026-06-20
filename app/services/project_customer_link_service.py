"""Project ↔ Customer association service.

Centralises the add/remove logic used by both the web project routes
(views/project.py) and the mobile API (api/v1/mobile_projects.py).

The service is framework-agnostic: it accepts plain arguments and returns
plain tuples, so callers handle their own HTTP responses. Permissions are
enforced here by using the access_control helpers, so neither caller has to
re-implement them.
"""

from app import db
from app.models.project import Project
from app.models.customer import Company
from app.models.project_customer_association import ProjectCustomerAssociation
from app.utils.access_control import can_view_project, can_view_company


class LinkError(Exception):
    """Raised when an add/remove call should map to a non-2xx HTTP response.

    `status` mirrors the HTTP status the caller should return. `message` is
    user-facing (already localised to Chinese; mobile API layer can localise
    further if needed).
    """
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def add_link(user, project_id, company_id):
    """Add a project ↔ customer association.

    Returns the new ProjectCustomerAssociation instance on success.
    Raises LinkError(status, message) on permission / validation / duplicate.

    Caller is responsible for committing (we only stage the add) so that
    a single web/mobile request can batch multiple operations.
    """
    if not project_id or not company_id:
        raise LinkError(400, '缺少必要参数')

    project = Project.query.get(project_id)
    if not project or project.is_deleted:
        raise LinkError(404, '项目不存在')
    if not can_view_project(user, project):
        raise LinkError(403, '没有权限访问此项目')

    company = Company.query.filter_by(id=company_id, is_deleted=False).first()
    if not company:
        raise LinkError(404, '指定的客户不存在')
    if not can_view_company(user, company):
        raise LinkError(403, '没有权限访问此客户')

    success, result = ProjectCustomerAssociation.add_association(
        project_id, company_id, created_by=user.id
    )
    if not success:
        # Duplicate (unique constraint on project_id+company_id) → 409 Conflict
        raise LinkError(409, result)
    return result


def remove_link(user, association_id):
    """Remove a project ↔ customer association.

    Permission model mirrors the web route at views/project.py:3851:
    admins can remove any link; everyone else can only remove the links
    they themselves created.

    Returns the deleted association_id on success; raises LinkError otherwise.
    Caller is responsible for committing.
    """
    association = ProjectCustomerAssociation.query.get(association_id)
    if not association:
        raise LinkError(404, '关联不存在')

    is_admin = getattr(user, 'role', None) == 'admin'
    is_creator = (
        getattr(association, 'created_by', None) is not None
        and association.created_by == user.id
    )
    if not (is_admin or is_creator):
        raise LinkError(403, '您只能移除自己添加的客户关联')

    success, message = ProjectCustomerAssociation.remove_association(association_id)
    if not success:
        raise LinkError(400, message)
    return association_id
