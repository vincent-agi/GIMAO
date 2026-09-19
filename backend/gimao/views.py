import os

from django.http import HttpResponse


def home_view(request):
    """
    Vue d'accueil avec liens vers les différentes sections
    """
    from dotenv import load_dotenv

    load_dotenv()

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8081")

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GIMAO - Accueil</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }}

            .container {{
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                padding: 50px;
                max-width: 800px;
                width: 100%;
            }}

            h1 {{
                color: #333;
                text-align: center;
                margin-bottom: 15px;
                font-size: 2.5em;
            }}

            .subtitle {{
                text-align: center;
                color: #666;
                margin-bottom: 40px;
                font-size: 1.1em;
            }}

            .links-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }}

            .link-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px;
                padding: 30px;
                text-align: center;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                cursor: pointer;
                text-decoration: none;
                display: block;
                color: white;
            }}

            .link-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            }}

            .link-card.admin {{
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            }}

            .link-card.swagger {{
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            }}

            .link-card.app {{
                background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            }}

            .link-icon {{
                font-size: 3em;
                margin-bottom: 15px;
            }}

            .link-title {{
                font-size: 1.5em;
                font-weight: bold;
                margin-bottom: 10px;
            }}

            .link-description {{
                font-size: 0.9em;
                opacity: 0.9;
            }}

            .footer {{
                text-align: center;
                margin-top: 40px;
                color: #666;
                font-size: 0.9em;
            }}

            @media (max-width: 768px) {{
                .container {{
                    padding: 30px;
                }}

                h1 {{
                    font-size: 2em;
                }}

                .links-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 GIMAO</h1>
            <p class="subtitle">Gestion Informatisée de Maintenance Assistée par Ordinateur</p>

            <div class="links-grid">
                <a href="{frontend_url}" class="link-card app" target="_blank">
                    <div class="link-icon">🚀</div>
                    <div class="link-title">Application GIMAO</div>
                    <div class="link-description">Interface principale de gestion</div>
                </a>

                <a href="/admin/" class="link-card admin">
                    <div class="link-icon">⚙️</div>
                    <div class="link-title">Django Admin</div>
                    <div class="link-description">Administration du système</div>
                </a>

                <a href="/swagger/" class="link-card swagger">
                    <div class="link-icon">📚</div>
                    <div class="link-title">API Documentation</div>
                    <div class="link-description">Documentation Swagger/OpenAPI</div>
                </a>
            </div>

            <div class="footer">
                <p>Version 1.0 | © 2025 GIMAO</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)
