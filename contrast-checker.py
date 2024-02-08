
def hexToRGB(hex):
    hex = hex.lstrip('#')
    return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))


def rgbToHex(rgb):
    return '#%02x%02x%02x' % rgb


def normalizeValue(value):
    val = value/255
    if val <= 0.04045:
        return val / 12.92
    return ((val + 0.055) / 1.055) ** 2.4


def getLuminance(color):
    """
    Get the relative luminance of a color according to WCAG 2.0 standards
    :param color:
    :return: float between 0 and 1
    """
    rgb = hexToRGB(color)
    return 0.2126 * normalizeValue(rgb[0]) + 0.7152 * normalizeValue(rgb[1]) + 0.0722 * normalizeValue(rgb[2])


def getContrastRatio(foreground, background):
    """
    Get the contrast ratio between two colors according to WCAG 2.0 standards
    :param foreground:
    :param background:
    :return: float between 1 and 21 to denote contrast ratio
    """
    fg = getLuminance(foreground)
    bg = getLuminance(background)

    if fg > bg:
        return (fg + 0.05) / (bg + 0.05)
    return (bg + 0.05) / (fg + 0.05)


def checkContrastLevel(contrastRatio):
    """
    Check the contrast ratio and return the level of contrast
    :param contrastRatio:
    :return:
    """
    print(f"Normal Text WCAG AA: {'Pass' if contrastRatio >= 4.5 else 'Fail'}")
    print(f"Large Text WCAG AA: {'Pass' if contrastRatio >= 3.0 else 'Fail'}")
    print(f"Normal Text WCAG AAA: {'Pass' if contrastRatio >= 7.0 else 'Fail'}")
    print(f"Large Text WCAG AAA: {'Pass' if contrastRatio >= 4.5 else 'Fail'}")


def getContrastsForColour(colour, contrasts):
    """
    Get all contrast ratios for a specific colour
    :param colour:
    :param contrasts:
    :return:
    """
    print(contrasts.items())
    filteredContrasts = {k: v for k, v in contrasts.items() if colour in v}
    return filteredContrasts


colours = {
    "black": "#000000",
    "dark-grey": "#53565A",
    "grey": "#63666A",
    "light-grey": "#A9A9A9",
    "very-light-grey": "#F6F6F6",
    "white": "#ffffff",
    "ng-blue": "#00148C",
    "blue": "#009DDC",
    "teal": "#00BFB3",
    "purple": "#500778",
    "magenta": "#C800A1",
    "lilac": "#AD96DC",
    "orange": "#FA4616",
    "mid-blue": "#0072CE",
    "soft-orange": "#FFB25B",
    "mid-green": "#547221",
    "light-blue": "#00AFF0",
    "red": "#F53C32",
    "green": "#3CE12D",
    "yellow": "#FADC00",
}
fgColours = colours.copy()
bgColours = colours.copy()
contrasts = {}

for key in bgColours:
    print("=====================================")
    print("Background: ", key)
    for key2 in fgColours:
        print("Foreground: ", key2)
        colourKey = tuple(sorted((key, key2)))
        if colourKey in contrasts:
            continue
        contrastRatio = getContrastRatio(fgColours[key2], bgColours[key])
        contrasts[colourKey] = contrastRatio
        print(f"Contrast Ratio of {key2} on {key} = {contrastRatio}")
        checkContrastLevel(contrastRatio)
        print("-------------------------------------")

sortedContrasts = dict(sorted( ((v,k) for k,v in contrasts.items()), reverse=True))
tealContrasts = getContrastsForColour("teal", sortedContrasts)
for k in tealContrasts:
    print(k, tealContrasts[k])
