def load_template(template_path, **kwargs):
    """
    Load an HTML template and replace placeholders with provided values.
    
    Args:
        template_path: Path to the HTML template file
        **kwargs: Key-value pairs to replace placeholders in the template
        
    Returns:
        String containing the processed HTML template
    """
    with open(template_path, 'r', encoding='utf-8') as file:
        template = file.read()
    
    # Replace placeholders with values
    for key, value in kwargs.items():
        placeholder = '{{' + key + '}}'
        template = template.replace(placeholder, str(value))
    
    return template

# Load CSS from external file
def load_css(st, css_file):
    with open(css_file, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def load_md(file_name):
    """
    Load an HTML template and replace placeholders with provided values.
    
    Args:
        file_name: Path to the HTML template file
        **kwargs: Key-value pairs to replace placeholders in the template
        
    Returns:
        String containing the processed HTML template
    """
    with open(f'ui/static/md/{file_name}', 'r', encoding='utf-8') as file:
        text = file.read()
    return text

def show_md_content(st, file_name, value):
    text = load_md(file_name)
    if text:
        content = f"""{text.format(value)}"""
        st.markdown(content, unsafe_allow_html=True,)