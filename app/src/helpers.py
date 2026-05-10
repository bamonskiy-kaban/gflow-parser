from dissect.target.target import Target

from dataclasses import dataclass
from typing import Optional


@dataclass
class TargetInfo:
    os: str
    hostname: str
    domain: Optional[str]
    version: Optional[str]
    ips: str


def get_target_info(target_path: str) -> TargetInfo:
    target = Target.open(target_path)

    if not hasattr(target, "os"):
        raise Exception(f"No OS plugin found for target: {target_path}")

    if not hasattr(target, "hostname"):
        raise Exception(f"No hostname found for target: {target_path}")

    hostname = getattr(target, "hostname")
    domain = getattr(target, "domain") if hasattr(target, "domain") else None

    os = getattr(target, "os")
    version = getattr(target, "version") if hasattr(target, "version") else None
    ips_list = getattr(target, "ips") if hasattr(target, "ips") else []
    ips = ",".join(ips_list)

    return TargetInfo(
        os=os,
        hostname=hostname,
        domain=domain,
        version=version,
        ips=ips
    )


def validate_index(index: str) -> bool:
    return True