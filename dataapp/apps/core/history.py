"""
History tracking utilities with change source support.

This module provides:
- ChangeSource enum for categorizing modification sources
- Context variable for passing change source through the call stack
- Signal handler for automatically populating change_source in history records
- HistoricalRecordsWithSource for creating history models with change_source field
"""
import contextvars
from django.db import models
from simple_history.models import HistoricalRecords
from simple_history.signals import pre_create_historical_record


class ChangeSource(models.TextChoices):
    """
    Enumeration of possible sources for data modifications.
    数据修改来源的枚举。
    """
    ADMIN = 'admin', 'Admin 管理后台'
    API = 'api', 'REST API'
    CELERY = 'celery', 'Celery 异步任务'
    SYNC = 'sync', 'Nextcloud 同步'
    SHELL = 'shell', 'Django Shell/脚本'
    ONLYOFFICE_IMPORT = 'onlyoffice_import', 'OnlyOffice 导入'
    UNKNOWN = 'unknown', '未知来源'


# Context variable for storing the current change source
# 用于存储当前修改来源的上下文变量
_change_source_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    'change_source',
    default=ChangeSource.UNKNOWN
)


def set_change_source(source: str) -> contextvars.Token:
    """
    Set the change source for the current context.
    设置当前上下文的修改来源。

    Args:
        source: One of ChangeSource values

    Returns:
        Token that can be used to reset the value

    Example:
        >>> token = set_change_source(ChangeSource.API)
        >>> # ... perform operations ...
        >>> reset_change_source(token)
    """
    return _change_source_var.set(source)


def get_change_source() -> str:
    """
    Get the current change source from context.
    从上下文获取当前修改来源。

    Returns:
        Current change source value
    """
    return _change_source_var.get()


def reset_change_source(token: contextvars.Token) -> None:
    """
    Reset the change source to its previous value.
    重置修改来源到之前的值。

    Args:
        token: Token returned by set_change_source
    """
    _change_source_var.reset(token)


class ChangeSourceContext:
    """
    Context manager for setting change source.
    用于设置修改来源的上下文管理器。

    Example:
        >>> with ChangeSourceContext(ChangeSource.API):
        ...     obj.save()  # History will record source as 'api'
    """

    def __init__(self, source: str):
        self.source = source
        self.token = None

    def __enter__(self):
        self.token = set_change_source(self.source)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token is not None:
            reset_change_source(self.token)
        return False


def populate_change_source(sender, **kwargs):
    """
    Signal handler to populate change_source field in historical records.
    信号处理器，用于在历史记录中填充 change_source 字段。

    This is connected to pre_create_historical_record signal.
    """
    history_instance = kwargs.get('history_instance')
    if history_instance is not None and hasattr(history_instance, 'change_source'):
        history_instance.change_source = get_change_source()


# Connect the signal handler
pre_create_historical_record.connect(
    populate_change_source,
    dispatch_uid='populate_change_source'
)


class ChangeSourceHistoricalModel(models.Model):
    """
    Abstract model that adds change_source field to historical records.
    为历史记录添加 change_source 字段的抽象模型。
    """
    change_source = models.CharField(
        max_length=20,
        choices=ChangeSource.choices,
        default=ChangeSource.UNKNOWN,
        verbose_name='修改来源',
        help_text='Source of the modification'
    )

    class Meta:
        abstract = True


class HistoricalRecordsWithSource(HistoricalRecords):
    """
    Custom HistoricalRecords that includes change_source field.
    包含 change_source 字段的自定义 HistoricalRecords。

    Usage:
        class MyModel(models.Model):
            name = models.CharField(max_length=100)
            history = HistoricalRecordsWithSource()

    This will create a historical model with an additional change_source field
    that tracks where the modification came from (admin, api, celery, etc.)
    """

    def __init__(self, **kwargs):
        # Add ChangeSourceHistoricalModel to bases
        bases = kwargs.get('bases', [models.Model])
        if not isinstance(bases, (list, tuple)):
            bases = [bases]
        bases = list(bases)

        # Insert ChangeSourceHistoricalModel at the beginning
        if ChangeSourceHistoricalModel not in bases:
            bases.insert(0, ChangeSourceHistoricalModel)

        kwargs['bases'] = bases
        super().__init__(**kwargs)
