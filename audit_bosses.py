import requests

# Configurações
WIKI_API = "https://tibia.fandom.com/api.php"
MY_API = "https://tibia-boss-api.onrender.com/api/v1/bosses"

def get_wiki_bosses():
    """Busca todos os títulos da categoria Bosses na Wiki"""
    print("📡 Consultando TibiaWiki...")
    bosses = set()
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": "Category:Bosses",
        "cmlimit": 500,
        "cmnamespace": 0,  # Apenas artigos principais
        "cmtype": "page",   # Garante que só pega páginas
        "format": "json"
    }
    
    while True:
        response = requests.get(WIKI_API, params=params).json()
        for member in response['query']['categorymembers']:
            if member['ns'] == 0:
                bosses.add(member['title'])
        
        if 'continue' in response:
            params['cmcontinue'] = response['continue']['cmcontinue']
        else:
            break
            
    return bosses

def get_my_api_bosses():
    """Busca todos os nomes cadastrados na nossa API usando paginação"""
    print("📡 Consultando Nossa API...")
    bosses = set()
    page = 1
    limit = 100
    
    while True:
        response = requests.get(f"{MY_API}?page={page}&limit={limit}").json()
        if 'items' not in response:
            print(f"❌ Erro ao buscar página {page}: {response}")
            break
            
        for item in response['items']:
            bosses.add(item['name'])
            
        if page >= response['pages']:
            break
        page += 1
        
    return bosses

def audit():
    wiki_set = get_wiki_bosses()
    db_set = get_my_api_bosses()

    print(f"\n📊 RESUMO:")
    print(f"Wiki Encontrou: {len(wiki_set)}")
    print(f"Banco Encontrou: {len(db_set)}")

    missing = wiki_set - db_set
    
    if missing:
        print(f"\n⚠️ Faltando no Banco ({len(missing)}):")
        # Vamos mostrar apenas os primeiros 20 se forem muitos
        sorted_missing = sorted(missing)
        for name in sorted_missing[:20]:
            print(f" - {name}")
        if len(missing) > 20:
            print(f" ... e mais {len(missing) - 20} itens.")
        print("\nNota: É normal faltar alguns se forem páginas de redirecionamento ou sem Infobox.")
    else:
        print("\n✅ SUCESSO TOTAL! O Banco contém todos os artigos da Wiki.")

if __name__ == "__main__":
    audit()
