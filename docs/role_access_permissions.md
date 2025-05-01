# 用户角色与数据访问权限设计

## 核心需求

- 不同账户之间不能看到对方的数据，除产品库数据外
- 渠道经理角色可以看到所有项目管理中的渠道跟进项目，但不能编辑和删除，不能看到其他人的客户信息
- 营销总监角色可以看到所有渠道跟进和销售重点项目，但不能编辑和删除不属于自己的项目
- 销售人员可以看到自己的项目不能看到其他账户的项目，但可以通过归属功能选择代理商角色
- 设计一个归属模型，用来管理账户下可以看到那些其他账户的数据，可以多选以账户为准，选中的能看到，但不能编辑，功能和账户默认的权限不冲突，是叠加
- 产品经理和解决方案经理可以看到所有的报价单信息
- 代理商和普通人员，只能看到自己的数据，不能通过归属功能获得其他账户的信息

## 数据模型设计

### 1. 归属模型 (Affiliation)

```python
class Affiliation(db.Model):
    __tablename__ = 'affiliations'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 数据所有者ID
    viewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 可查看者ID
    created_at = db.Column(db.Float, default=time.time)  # 创建时间
    
    # 与User模型的关系
    owner = db.relationship('User', foreign_keys=[owner_id], backref=db.backref('shared_with', lazy='dynamic'))
    viewer = db.relationship('User', foreign_keys=[viewer_id], backref=db.backref('can_view_from', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('owner_id', 'viewer_id', name='uix_owner_viewer'),
    )
```

### 2. 修改现有模型，添加所有者字段

需要为以下模型添加所有者字段：

```python
# 公司模型
class Company(db.Model):
    # 现有字段...
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', backref=db.backref('companies', lazy='dynamic'))

# 联系人模型
class Contact(db.Model):
    # 现有字段...
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', backref=db.backref('contacts', lazy='dynamic'))

# 项目模型
class Project(db.Model):
    # 现有字段...
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', backref=db.backref('projects', lazy='dynamic'))
    project_type = db.Column(db.String(50))  # 'channel_follow', 'sales_focus', 'normal'

# 报价单模型
class Quotation(db.Model):
    # 现有字段...
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', backref=db.backref('quotations', lazy='dynamic'))
```

### 3. 扩展用户角色类型

- 管理员 (admin): 拥有所有权限
- 销售人员 (sales): 管理自己的客户、项目和报价
- 产品经理 (product): 管理产品和查看所有报价
- 解决方案经理 (solution): 查看所有报价和编辑项目
- 渠道经理 (channel_manager): 查看所有渠道跟进项目
- 营销总监 (marketing_director): 查看所有渠道跟进和销售重点项目
- 代理商 (dealer): 仅查看自己的数据
- 普通用户 (user): 仅查看自己的数据

## 核心查询逻辑

通用数据访问控制函数，根据用户角色和权限返回可查看的数据集:

```python
def get_viewable_data(model_class, current_user, special_filters=None):
    # 产品数据不受限制
    if model_class.__name__ == 'Product':
        return model_class.query.filter(*special_filters if special_filters else [])
    
    # 管理员可以查看所有数据
    if current_user.role == 'admin':
        return model_class.query.filter(*special_filters if special_filters else [])
    
    # 处理特殊角色权限
    if model_class.__name__ == 'Project':
        # 渠道经理：可以查看所有渠道跟进项目 + 自己的项目
        if current_user.role == 'channel_manager':
            return model_class.query.filter(
                db.or_(
                    model_class.owner_id == current_user.id,
                    model_class.project_type == 'channel_follow'
                ),
                *special_filters if special_filters else []
            )
        
        # 营销总监：可以查看所有渠道跟进和销售重点项目 + 自己的项目
        if current_user.role == 'marketing_director':
            return model_class.query.filter(
                db.or_(
                    model_class.owner_id == current_user.id,
                    model_class.project_type.in_(['channel_follow', 'sales_focus'])
                ),
                *special_filters if special_filters else []
            )
    
    # 报价单特殊权限
    if model_class.__name__ == 'Quotation':
        # 产品经理和解决方案经理可以查看所有报价单
        if current_user.role in ['product', 'solution']:
            return model_class.query.filter(*special_filters if special_filters else [])
    
    # 客户特殊权限处理
    if model_class.__name__ in ['Company', 'Contact']:
        # 渠道经理不能看到其他账户的客户信息
        if current_user.role == 'channel_manager':
            return model_class.query.filter(
                model_class.owner_id == current_user.id,
                *special_filters if special_filters else []
            )
    
    # 标准数据访问控制：自己的数据 + 归属关系授权的数据
    viewable_user_ids = [current_user.id]
    
    # 代理商和普通用户只能看到自己的数据
    if current_user.role not in ['dealer', 'user']:
        # 获取通过归属关系可以查看的数据
        affiliations = Affiliation.query.filter_by(viewer_id=current_user.id).all()
        for affiliation in affiliations:
            viewable_user_ids.append(affiliation.owner_id)
    
    return model_class.query.filter(
        model_class.owner_id.in_(viewable_user_ids),
        *special_filters if special_filters else []
    )
```

## API接口设计

1. 获取用户的归属关系 - GET /api/v1/users/{user_id}/affiliations
2. 添加用户归属关系 - POST /api/v1/users/{user_id}/affiliations
3. 删除归属关系 - DELETE /api/v1/affiliations/{affiliation_id}
4. 获取可用数据来源用户 - GET /api/v1/users/{user_id}/available_owners

## 数据编辑控制

基于数据所有权的编辑控制:

```python
def can_edit_data(model_obj, current_user):
    # 管理员有全部编辑权限
    if current_user.role == 'admin':
        return True
    
    # 只有数据所有者才能编辑
    return model_obj.owner_id == current_user.id
```

## 前端实现

1. 用户详情页中添加"归属管理"标签页
2. 扩展用户角色选项
3. 项目创建/编辑页面添加项目类型选择
4. 在用户列表页面添加归属管理入口

## 功能总结

通过以上设计实现了:

1. **数据隔离**:
   - 每个数据记录有明确的所有者
   - 默认情况下，用户只能看到自己创建的数据
   - 不同账户之间的数据完全隔离

2. **角色权限**:
   - 管理员可以查看和编辑所有数据
   - 渠道经理可以查看所有渠道跟进项目，但不能编辑不属于自己的项目
   - 营销总监可以查看所有渠道跟进和销售重点项目，但不能编辑不属于自己的项目
   - 产品经理和解决方案经理可以查看所有报价单
   - 代理商和普通用户只能查看自己的数据

3. **归属管理**:
   - 通过归属关系，可以让特定用户查看其他用户的数据
   - 归属关系由管理员配置
   - 用户只能查看而不能编辑这些通过归属获得访问权的数据

4. **产品数据共享**:
   - 产品库数据不受隔离限制，所有用户都可以访问 