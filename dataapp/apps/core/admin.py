"""
Base admin classes with history tracking support.
"""
from simple_history.admin import SimpleHistoryAdmin
from .history import ChangeSource, set_change_source, reset_change_source


class BaseHistoryAdmin(SimpleHistoryAdmin):
    """
    Base admin class that automatically sets change_source to ADMIN.
    自动将 change_source 设置为 ADMIN 的基础管理类。

    All ModelAdmin classes that use history tracking should inherit from this class.
    所有使用历史追踪的 ModelAdmin 类都应该继承此类。

    Example:
        @admin.register(MyModel)
        class MyModelAdmin(BaseHistoryAdmin):
            list_display = ['name', 'created_at']
    """

    def save_model(self, request, obj, form, change):
        """
        Override save_model to set change_source before saving.
        重写 save_model 以在保存前设置 change_source。
        """
        token = set_change_source(ChangeSource.ADMIN)
        try:
            super().save_model(request, obj, form, change)
        finally:
            reset_change_source(token)

    def delete_model(self, request, obj):
        """
        Override delete_model to set change_source before deleting.
        重写 delete_model 以在删除前设置 change_source。
        """
        token = set_change_source(ChangeSource.ADMIN)
        try:
            super().delete_model(request, obj)
        finally:
            reset_change_source(token)

    def save_formset(self, request, form, formset, change):
        """
        Override save_formset to set change_source for inline saves.
        重写 save_formset 以为内联保存设置 change_source。
        """
        token = set_change_source(ChangeSource.ADMIN)
        try:
            super().save_formset(request, form, formset, change)
        finally:
            reset_change_source(token)
