"""The module contains some common functions."""

import asyncio
import base64
import hashlib
import json
import logging
import os
import platform
import re
import uuid
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Union
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import aiofiles
import httpx
from PIL import Image
from pydantic import AnyUrl

logger = logging.getLogger(__name__)
Image.MAX_IMAGE_PIXELS = 400000000


def is_linux():
    return platform.system().lower() == "linux"


def get_mac_address():
    mac_address = "-".join(
        [
            "{:02x}".format((uuid.getnode() >> elements) & 0xFF)
            for elements in range(0, 2 * 6, 2)
        ][::-1]
    )
    return mac_address


def get_timestamp():
    return str(datetime.now().timestamp())


def get_format_time():
    """Yyyy-MM-dd HH:mm:ss."""
    """yyyy-MM-dd HH:mm:ss.SSS"""
    """yyyy-MM-dd HH:mm:ss.SSSSSSSSS"""
    now = datetime.now()
    nano_str = "{:09d}".format(
        now.microsecond * 1000
    )  # convert micro second to nano second
    current_time = now.strftime("%Y-%m-%d %H:%M:%S.") + nano_str
    return current_time


def chunk_list(lst, chunk_size=2):
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def extract_first_json(text):
    matches = re.findall(r"```[\n]*json(.*?)```", text, re.DOTALL)
    json_texts = [match.strip() for match in matches]
    json_text = json_texts[0] if json_texts else text
    if not json_text.startswith("{") or not json_text.endswith("}"):
        json_text = json_text[json_text.find("{") : json_text.rfind("}") + 1]
    return json_text


def extract_json_str(text: str) -> str:
    """Extract JSON string from text.

    Only works for single JSON string.
    """
    # NOTE: this regex parsing is taken from langchain.output_parsers.pydantic
    match = re.search(r"\{.*\}", text.strip(), re.MULTILINE | re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError(f"Could not extract json string from output: {text}")

    return match.group()


async def source_to_bytes(source: str):
    if source.startswith("http"):
        async with httpx.AsyncClient() as client:
            http_response = await client.get(source)
            http_response.raise_for_status()
            return http_response.content
    else:
        async with aiofiles.open(source, "rb") as f:
            return await f.read()


async def image_to_base64(source: str, max_image_pixels: int = 10000000) -> str:
    image_bytes = await source_to_bytes(source)

    def process_image(image_bytes):
        with Image.open(BytesIO(image_bytes)) as img:
            width, height = img.size
            current_pixels = width * height

            # Reduce size 50% each time until it's under max_pixels
            if current_pixels > max_image_pixels:
                scale = (max_image_pixels / current_pixels) ** 0.5
                new_width = max(1, int(width * scale))
                new_height = max(1, int(height * scale))
                img = img.resize((new_width, new_height), Image.LANCZOS)

            # Save as bytes
            output = BytesIO()
            img_format = img.format if img.format else "PNG"
            img.save(output, format=img_format)
            return output.getvalue()

    image_bytes = await asyncio.to_thread(process_image, image_bytes)
    ext = os.path.splitext(source)[-1][1: ]
    return f"data:image/{ext};base64,{base64.b64encode(image_bytes).decode('utf-8')}"


# 512 * 1024 * 1024 bytes == 512MB
async def video_to_base64(source: str, max_video_size: int = 512 * 1024 * 1024) -> str:
    video_bytes = await source_to_bytes(source)
    if len(video_bytes) > max_video_size:
        return source
    else:
        ext = os.path.splitext(source)[-1][1: ]
        return f"data:video/{ext};base64,{base64.b64encode(video_bytes).decode('utf-8')}"


def append_url_path(url, path):
    parsed = urlparse(str(url))
    final_path = parsed.path.rstrip("/") + "/" + path.lstrip("/")
    return urlunparse(parsed._replace(path=final_path))


def build_url(
    base_url: Union[AnyUrl, str], path: str = "", query_params: Dict[str, Any] = None
) -> str:
    """Convert base_url to a URL object, append path, and append query parameters."""
    parsed = urlparse(str(base_url))
    # Append path
    final_path = parsed.path
    if path:
        final_path = final_path.rstrip("/") + "/" + path.lstrip("/")
    # Append query
    original_query = dict(parse_qsl(parsed.query))
    query_params = query_params or {}
    merged_query = {**original_query, **query_params}
    final_query = urlencode(merged_query, doseq=True)
    # Return new url
    return urlunparse(parsed._replace(path=final_path, query=final_query))


def print_tree(node, prefix="", is_root=True, is_last=True, logger=None):
    # Print branch symbol
    branch = "└── " if is_last else "├── "
    if is_root:
        branch = ""
    line = prefix + branch + node.get("name", "")

    if logger:
        logger.info(line)
    else:
        print(line)

    children = node.get("children", [])
    for idx, child in enumerate(children):
        child_is_last = idx == len(children) - 1
        # Next layer prefix: uss " " for last one and "│" for others
        extension = "    " if is_last else "│   "
        if is_root:
            extension = ""
        print_tree(child, prefix + extension, False, child_is_last, logger)


def filter_json_types(d):
    result = {}
    for k, v in d.items():
        if isinstance(v, (str, int, float, bool, list, dict, type(None))):
            result[k] = v
        else:
            result[k] = "..."
    return result


def msgpack_preprocess(obj):
    # The 3 types of objects that can be serialized by msgpack
    if obj is None or isinstance(obj, (bool, int, float, str, bytes)):
        return obj
    # Tuples are converted to lists recursively
    elif isinstance(obj, (list, tuple, set)):
        return [msgpack_preprocess(item) for item in obj]
    elif isinstance(obj, dict):
        # The keys of a dict must be strings, etc
        return {str(k): msgpack_preprocess(v) for k, v in obj.items()}
    else:
        # For other types, convert to string
        return str(obj)


def get_md5(arg_str):
    md5 = hashlib.md5()
    md5.update(arg_str.encode("utf-8"))
    md5_value = md5.hexdigest()
    return md5_value


def to_json(obj):
    if isinstance(obj, str):
        return obj
    return json.dumps(obj, ensure_ascii=False, default=str)


def process_attachments(attachments):
    query_attachments = []
    for attachment in attachments:
        if not attachment.startswith("http") and not os.path.exists(attachment):
            logger.warning(f"Attachment file not found: {attachment}")
            continue

        if attachment.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
            query_attachments.append(
                {
                    "type": "image_url",
                    "image_url": {"url": attachment},
                }
            )
        elif attachment.endswith((".mp4", ".avi", ".mov", ".wmv", ".flv")):
            query_attachments.append(
                {
                    "type": "video_url",
                    "video_url": {"url": attachment},
                }
            )
    return query_attachments
