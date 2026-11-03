"""Editorial settings shared by metadata and APK configuration consumers."""


def foreign_category(entry):
    value = entry.get('foreign_category', True)
    if not isinstance(value, bool):
        raise ValueError('foreign_category must be a boolean')
    return value


# Stable client identifiers, independent of the library README collection titles.
APP_CATEGORIES = {
    'Productivity': 'productivity', 'Browsers': 'browsers', 'Creativity': 'creativity',
    'Maps': 'maps', 'Health & fitness': 'health', 'Social': 'social', 'Books': 'books',
    'Food & drink': 'foodanddrink', 'Smart home': 'smarthome', 'Work': 'business',
    'Finance': 'finance', 'Shopping': 'purchases', 'Music': 'music', 'Video': 'video',
    'AI assistants': 'ai', 'News': 'news', 'Dating': 'dating', 'Messaging': 'messengers',
    'Security': 'security', 'Music education': 'musiceducation',
    'Entertainment': 'entertainment', 'Tools': 'tools', 'Auto & vehicles': 'transport',
}


def category_slugs(entry):
    category = entry.get('category')
    if category is None:
        return []
    if not isinstance(category, str) or category not in APP_CATEGORIES:
        raise ValueError('Unknown application category')
    return [APP_CATEGORIES[category]]
