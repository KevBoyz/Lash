# Configure file, edit only the values of keys.
# Read the docstring


def config():
    """
    Configuration guide; Description of keys.

    * black_list: List of processes to be killed by _taskkiller_,
     - insert the process name + extension in srt type, like: 'process.exe' or if you are in Linux: 'process'
     - Be careful what you add to this list, you may receive permission errors when terminating certain processes.
    * html, css and js code: The default code that the files of _web new_ command will have.
    """
    return \
        {
            'black_list': [],
            'html_code': """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="style.css">
    <title></title>
</head>
<body>
    <header></header>
    <main>
        
    </main>
    <footer></footer>

    <script src="script.js"></script>
</body>
</html>""".strip(),
            'css_code': """""",
            'js_code': """""",
        }
