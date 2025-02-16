from aiohttp import web
import aiohttp_jinja2
import jinja2
import aiohttp

app = web.Application()

aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))


async def home(request):
    if request.method == 'POST':
        data = await request.post()
        user_text = data.get('text', '')

        # Call LanguageTool API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.languagetool.org/v2/check',
                data={'text': user_text, 'language': 'en-US'}
            ) as response:
                result = await response.json()

        # Extract suggestions from the response
        corrections = []
        for match in result.get('matches', []):
            replacement = match['replacements'][0]['value'] if match['replacements'] else None
            if replacement:
                corrections.append((match['offset'], match['length'], replacement))

        # Apply corrections to the original text
        corrected_text = user_text
        for offset, length, replacement in reversed(corrections):
            corrected_text = corrected_text[:offset] + replacement + corrected_text[offset + length:]

        return aiohttp_jinja2.render_template(
            'home.html', request, {'original': user_text, 'corrected': corrected_text}
        )

    return aiohttp_jinja2.render_template('home.html', request, {'original': None, 'corrected': None})


app.router.add_route('*', '/', home)
app.router.add_static('/static/', path='static', name='static')

if __name__ == '__main__':
    web.run_app(app, host='127.0.0.1', port=8080)
