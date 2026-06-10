import xml.etree.ElementTree as ET
from PIL import Image

# Convert .plist-style array to (two-dimensional) tuple
# Examples:
# "{5, 10}" -> (5.0, 10.0)
# "{{1, 2}, {3, 4}}" -> ((1.0, 2.0), (3.0, 4.0))
def parse_array(array_string):
    array_string = array_string.replace(" ", "")[1:-1]
    comma_count = array_string.count(",")

    if comma_count == 1:
        # One-dimensional array
        return tuple(map(float, array_string.split(",")))

    elif comma_count == 3:
        # Two-dimensional array
        # Split into two arrays and recursively parse them both
        array_1, array_2 = array_string.split("},")
        array_1 += "}"
        return (parse_array(array_1), parse_array(array_2))

# Parses the XML texture data for each texture in the spritesheet
def parse_sprite_data(sprite_data):
    sprite_offset = ()
    sprite_texture_rect = ()
    sprite_source_size = ()
    sprite_rotated = False

    for i, element in enumerate(sprite_data):
        if element.text == "spriteOffset":
            sprite_offset = parse_array(sprite_data[i + 1].text)

        elif element.text == "textureRect":
            sprite_texture_rect = parse_array(sprite_data[i + 1].text)

        elif element.text == "spriteSourceSize":
            sprite_source_size = parse_array(sprite_data[i + 1].text)

        elif element.text == "textureRotated":
            # Tag name is either "true" or "false", convert to boolean
            sprite_rotated = "t" in sprite_data[i + 1].tag

    corner = sprite_texture_rect[0]
    size = sprite_texture_rect[1]
    if sprite_rotated:
        size = size[::-1]
    # The sprite's texture rect is actually its offset THEN its size
    sprite_texture_rect = (*corner, corner[0] + size[0], corner[1] + size[1])

    return {
        "offset": sprite_offset,
        "texture_rect": sprite_texture_rect,
        "source_size": sprite_source_size,
        "rotated": sprite_rotated
    }

# Return a dictionary with keys being texture names and values
# containing the image object and its coordinate offsets
def split_spritesheet(image_path, plist_path):
    spritesheet = Image.open(image_path).convert("RGBA")

    root = ET.parse(plist_path).getroot()
    sprites = root[0][1]

    split_sprites = {}
    texture_name = ""
    for element in sprites:
        if element.tag == "key":
            texture_name = element.text

        else:
            sprite_data = parse_sprite_data(element)

            sprite_image = spritesheet.crop(sprite_data["texture_rect"])
            if sprite_data["rotated"]:
                # No resampling filter here since rotation with multiples of 90
                # are lossless
                sprite_image = sprite_image.rotate(90, expand=True)

            sprite_image = sprite_image.crop(sprite_image.getbbox())

            split_sprites[texture_name] = {
                "image": sprite_image,
                "offset": sprite_data["offset"]
            }

    return split_sprites

# Parses the XML animdesc data for each layer in *-AnimDesc.plist
def parse_animdesc_sprite(animdesc_element):
    sprite_animdesc = {}

    key = ""
    for element in animdesc_element:
        if element.tag == "key":
            key = element.text

        elif key in ("position", "scale", "flipped"):
            sprite_animdesc[key] = parse_array(element.text)

        elif key == "rotation":
            sprite_animdesc[key] = float(element.text)

    return sprite_animdesc

def parse_animdesc(target_element):
    animdesc = {}

    for i, element in enumerate(target_element):
        if element.tag == "key":
            tag = int(element.text[7:])
            animdesc_element = target_element[i + 1]

            animdesc.update({
                tag: parse_animdesc_sprite(animdesc_element)
            })

    return animdesc

def get_animdesc(plist_path, animation_frame):
    with open(plist_path) as file:
        # The animdesc .plists have a leading newline and for some reason
        # that makes the XML parser error out so we remove it
        file_string = file.read().strip()
        root = ET.fromstring(file_string)[0][3]

    for i, element in enumerate(root):
        if element.text.startswith(animation_frame):
            target_element = root[i + 1]
            break

    return parse_animdesc(target_element)
