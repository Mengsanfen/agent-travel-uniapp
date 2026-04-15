from typing import Any

from pydantic import BaseModel, Field, field_validator

# 登陆参数
class ConversationsDataParams(BaseModel):
    # 会话id
    sessionId: str

    # 自定义参数校验
    @field_validator("sessionId",  mode='before')
    def check_not_empty(cls, v: Any, info: Any) -> Any:
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"{info.field_name}的值不能为空")
        return v


# 获取经纬度
class LocationDataParams(BaseModel):
    # 会话id
    content: str

    # 自定义参数校验
    @field_validator("content",  mode='before')
    def check_not_empty(cls, v: Any, info: Any) -> Any:
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"{info.field_name}的值不能为空")
        return v


class ExportPlanPdfParams(BaseModel):
    title: str = "旅行规划"
    content: str
    maps: list[dict[str, Any]] = Field(default_factory=list)
    export_type: str = "pdf"

    @field_validator("content", mode='before')
    def check_content_not_empty(cls, v: Any, info: Any) -> Any:
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"{info.field_name}不能为空")
        return v


class ArchivePlanParams(ExportPlanPdfParams):
    note: str = ""
    source_thread_id: str = ""


class UpdateArchiveParams(BaseModel):
    title: str | None = None
    note: str | None = None
