from datetime import datetime

from sqlmodel import Field, SQLModel


class TravelArchive(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    openid: str = Field(index=True)
    title: str = Field(default="旅行规划报告", index=True)
    note: str = Field(default="")
    filename: str = Field(default="")
    file_url: str = Field(default="")
    export_type: str = Field(default="pdf")
    source_thread_id: str = Field(default="", index=True)
    content_preview: str = Field(default="")
    route_count: int = Field(default=0)
    marker_count: int = Field(default=0)
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
