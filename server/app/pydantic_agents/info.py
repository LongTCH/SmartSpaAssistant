import re
from dataclasses import dataclass
from datetime import datetime

from app.configs.database import async_session
from app.pydantic_agents.model_hub import model_hub
from app.repositories import guest_info_repository
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext


@dataclass
class InfoAgentDeps:
    user_id: str


class InfoAgentOutput(BaseModel):
    fullname: str = Field(
        default="",
        description="Full name of the guest (must be at least 2 characters long), empty string if don't find information",
    )
    email: str = Field(
        default="",
        description="Email of the guest (must be valid email format: example@domain.com), empty string if don't find information",
    )
    phone: str = Field(
        default="",
        description="Phone number of the guest (must contain 8-15 digits), empty string if don't find information",
    )
    gender: str = Field(
        default="",
        description="Gender of the guest (male/female), empty string if don't find information",
    )
    birthday: str = Field(
        default="",
        description="Birthday of the guest (must be in YYYY-MM-DD format, cannot be in future or older than 150 years), empty string if don't find information",
    )
    address: str = Field(
        default="",
        description="Address of the guest (must be at least 5 characters long), empty string if don't find information",
    )


instructions = """
You are a helpful ai extractor.
Your task is to extract some information of guest from the conversation.
Please follow format.
"""

model = model_hub["gemini-1.5-flash-8b"]
info_agent = Agent(
    model=model,
    instructions=instructions,
    retries=2,
    output_type=InfoAgentOutput,
    output_retries=2,
)


@info_agent.output_validator
async def validate_output(
    ctx: RunContext[InfoAgentDeps], output: InfoAgentOutput
) -> InfoAgentOutput:
    user_id = ctx.deps.user_id
    async with async_session() as session:
        try:
            # Lấy thông tin khách hàng hiện tại
            guest_info = await guest_info_repository.get_guest_info_by_guest_id(
                session, user_id
            )

            if not guest_info:
                raise RuntimeError(
                    f"Guest information not found for user_id: {user_id}"
                )

            updated_fields = []

            # Cập nhật từng trường nếu không phải empty string và validate thành công
            if output.fullname and output.fullname.strip():
                try:
                    # Validate fullname
                    cleaned_fullname = " ".join(output.fullname.split())
                    if len(cleaned_fullname.strip()) >= 2:
                        guest_info.fullname = output.fullname
                        updated_fields.append(f"fullname: {output.fullname}")
                except:
                    pass  # Bỏ qua nếu không hợp lệ

            if output.email and output.email.strip():
                try:
                    # Validate email format
                    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    if re.match(email_pattern, output.email):
                        guest_info.email = output.email
                        updated_fields.append(f"email: {output.email}")
                except:
                    pass  # Bỏ qua nếu không hợp lệ

            if output.phone and output.phone.strip():
                try:
                    # Validate phone number
                    digits_only = re.sub(r"\D", "", output.phone)
                    if 8 <= len(digits_only) <= 15:
                        guest_info.phone = output.phone
                        updated_fields.append(f"phone: {output.phone}")
                except:
                    pass  # Bỏ qua nếu không hợp lệ

            if output.gender and output.gender.strip():
                try:
                    # Validate gender
                    if output.gender.lower() in ["male", "female"]:
                        guest_info.gender = output.gender.lower()
                        updated_fields.append(f"gender: {output.gender.lower()}")
                except:
                    pass  # Bỏ qua nếu không hợp lệ

            if output.birthday and output.birthday.strip():
                try:
                    # Parse birthday string thành datetime object (chỉ hỗ trợ YYYY-MM-DD)
                    parsed_birthday = datetime.strptime(output.birthday, "%Y-%m-%d")
                    # Check if date is reasonable (not in future, not too old)
                    current_year = datetime.now().year
                    if (
                        parsed_birthday.year <= current_year
                        and parsed_birthday.year >= (current_year - 150)
                    ):
                        guest_info.birthday = parsed_birthday
                        updated_fields.append(f"birthday: {output.birthday}")
                except:
                    pass  # Bỏ qua nếu không hợp lệ

            if output.address and output.address.strip():
                try:
                    # Validate address
                    cleaned_address = " ".join(output.address.split())
                    if len(cleaned_address.strip()) >= 5:
                        guest_info.address = output.address
                        updated_fields.append(f"address: {output.address}")
                except:
                    pass  # Bỏ qua nếu không hợp lệ

            # Nếu có trường nào được cập nhật thì commit
            if updated_fields:
                await guest_info_repository.update_guest_info(session, guest_info)
                await session.commit()

        except Exception as e:
            await session.rollback()
    return output
