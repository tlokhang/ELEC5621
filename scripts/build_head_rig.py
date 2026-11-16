"""Generate a kinematically supported Microduck head/neck MJCF from upstream."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "assets" / "microduck"
SOURCE = MODEL_DIR / "robot_groundcontact.xml"
OUTPUT = MODEL_DIR / "head_neck_rig.xml"
REMOVED_BRANCHES = {"yaw2roll", "bearing_roll"}


def main() -> None:
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    tree = ET.parse(SOURCE, parser=parser)
    root = tree.getroot()
    root.set("model", "microduck_head_neck_rig")

    worldbody = root.find("worldbody")
    if worldbody is None:
        raise ValueError("Upstream MJCF has no worldbody")
    trunk = worldbody.find("body[@name='trunk_base']")
    if trunk is None:
        raise ValueError("Upstream MJCF has no trunk_base body")

    # Keep the trunk and exact neck/head chain, while removing both leg branches.
    found_branches = {child.get("name") for child in trunk.findall("body")} & REMOVED_BRANCHES
    if found_branches != REMOVED_BRANCHES:
        raise ValueError(f"Upstream leg branches changed: {found_branches}")
    for child in list(trunk.findall("body")):
        if child.get("name") in REMOVED_BRANCHES:
            trunk.remove(child)
    kept_joints = {joint.get("name") for joint in root.findall(".//worldbody//joint")}
    for freejoint in list(trunk.findall("freejoint")):
        trunk.remove(freejoint)
    trunk.set("mocap", "true")

    actuator = root.find("actuator")
    if actuator is None:
        raise ValueError("Upstream MJCF has no actuator section")
    for item in list(actuator):
        joint_name = item.get("joint")
        if joint_name not in kept_joints:
            actuator.remove(item)

    expected = {"neck_pitch", "head_pitch", "head_yaw", "head_roll"}
    if expected != kept_joints:
        raise ValueError(f"Unexpected retained joint set: {kept_joints}")

    ET.indent(tree, space="  ")
    tree.write(OUTPUT, encoding="utf-8", xml_declaration=True)
    print(f"Wrote {OUTPUT}")
    print(f"Retained joints: {', '.join(sorted(expected))}")
    print(f"Removed leg branches: {', '.join(sorted(REMOVED_BRANCHES))}")


if __name__ == "__main__":
    main()
