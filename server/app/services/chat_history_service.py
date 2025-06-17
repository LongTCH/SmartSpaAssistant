import xml.etree.ElementTree as ET

from app.utils.agent_utils import MessagePart


async def agent_messages_to_xml(user_input: str, message_parts: list[MessagePart]):
    root = ET.Element("chat_histories")

    user_chat_elem = ET.SubElement(root, "chat")

    user_role_elem = ET.SubElement(user_chat_elem, "role")
    user_role_elem.text = "user"

    user_content_elem = ET.SubElement(user_chat_elem, "content")
    user_message_elem = ET.SubElement(user_content_elem, "message")
    user_type_elem = ET.SubElement(user_message_elem, "type")
    user_type_elem.text = "text"
    user_payload_elem = ET.SubElement(user_message_elem, "payload")
    user_payload_elem.text = user_input

    assistant_chat_elem = ET.SubElement(root, "chat")
    assistant_role_elem = ET.SubElement(assistant_chat_elem, "role")
    assistant_role_elem.text = "assistant"
    assistant_content_elem = ET.SubElement(assistant_chat_elem, "content")
    for message_part in message_parts:
        message_elem = ET.SubElement(assistant_content_elem, "message")
        type_elem = ET.SubElement(message_elem, "type")
        type_elem.text = message_part.type
        payload_elem = ET.SubElement(message_elem, "payload")
        payload_elem.text = message_part.payload
    return ET.tostring(root, encoding="unicode")


async def agent_output_to_xml(message_parts: list[MessagePart]) -> str:
    """
    Converts a list of MessagePart objects from an agent's output to an XML string.
    """
    root = ET.Element("messages")

    for message_part in message_parts:
        message_elem = ET.SubElement(root, "message")
        type_elem = ET.SubElement(message_elem, "type")
        type_elem.text = message_part.type
        payload_elem = ET.SubElement(message_elem, "payload")
        # Ensure payload is a string, as ET.Element.text expects a string
        payload_elem.text = str(message_part.payload)

    return ET.tostring(root, encoding="unicode")
