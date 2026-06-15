import threading
import time
import webbrowser
import os
import subprocess


def limpar_ngrok():
    """Tenta matar qualquer processo ngrok residual."""
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'ngrok.exe'],
                       capture_output=True, timeout=5)
    except Exception:
        pass
    try:
        from pyngrok import ngrok as nk
        nk.kill()
    except Exception:
        pass
    time.sleep(1)


def get_ngrok_path():
    from pyngrok import conf
    return conf.PyngrokConfig().ngrok_path


def run_flask():
    from app import create_app
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


def verificar_ngrok():
    try:
        import yaml
        ngrok_path = get_ngrok_path()
        config_path = os.path.join(os.path.dirname(ngrok_path), 'ngrok.yml')
        if not os.path.exists(config_path):
            return False
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        if not config:
            return False
        token = config.get('authtoken') or (config.get('agent') or {}).get('authtoken')
        return bool(token)
    except Exception:
        return False


def configurar_ngrok(token):
    ngrok_path = get_ngrok_path()
    try:
        subprocess.run(
            [ngrok_path, 'config', 'add-authtoken', token],
            capture_output=True, timeout=10
        )
        return True
    except Exception:
        return False


CREDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Estoque3D_creds')

def main():
    limpar_ngrok()
    from app.services.backup import criar_backup
    backup_nome = criar_backup()
    if backup_nome:
        print(f"[BACKUP] Banco salvo: {backup_nome}")
    else:
        print("[BACKUP] Nenhum banco para backup (primeira execucao)")

    print("Iniciando servidor Flask...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(2)

    if not verificar_ngrok():
        arquivo_token = os.path.join(CREDS_DIR, 'ngrok_token.txt')
        token = os.environ.get('NGROK_AUTHTOKEN')
        if not token and os.path.exists(arquivo_token):
            with open(arquivo_token, 'r') as f:
                token = f.read().strip()
        if not token:
            print()
            print("=" * 55)
            print("   CONFIGURACAO DO NGROK NECESSARIA")
            print("=" * 55)
            print()
            print("  O ngrok precisa de um token de acesso gratuito.")
            print()
            print("  1. Acesse: https://dashboard.ngrok.com/signup")
            print("     (crie uma conta gratis - leva 1 minuto)")
            print()
            print("  2. Apos login, va em:")
            print("     https://dashboard.ngrok.com/get-started/your-authtoken")
            print()
            print("  3. Copie o token (ex: 2aBcD...XyZk)")
            print()
            token = input("  Token: ").strip()

        if not token:
            print("\n  Token nao informado. Encerrando.")
            input("\nPressione Enter para sair...")
            return

        arquivo_token = os.path.join(CREDS_DIR, 'ngrok_token.txt')
        with open(arquivo_token, 'w') as f:
            f.write(token)

        if not configurar_ngrok(token):
            print("\n  [ERRO] Falha ao configurar o token.")
            print("  Tente executar manualmente:")
            print(f'  "{get_ngrok_path()}" config add-authtoken SEU_TOKEN')
            input("\nPressione Enter para sair...")
            return

        print("\n  Token configurado com sucesso!\n")
        time.sleep(2)

    try:
        from pyngrok import ngrok, conf
        conf.get_default().region = 'sa'
        public_url = ngrok.connect(5000, bind_tls=True)
        url = public_url.public_url
    except Exception as e:
        print(f"\n[ERRO] Nao foi possivel iniciar o tunel ngrok: {e}")
        print("Verifique sua conexao com a internet e o token.")
        input("\nPressione Enter para sair...")
        return

    print()
    print("=" * 55)
    print("          ESTOQUE 3D - ACESSO REMOTO")
    print("=" * 55)
    print()
    print(f"  URL PUBLICA:   {url}")
    print()
    print("  Compartilhe este link com qualquer pessoa")
    print("  para acessar o sistema pela internet.")
    print()
    print("  ATENCAO: O link fica ativo apenas enquanto")
    print("  esta janela estiver ABERTA.")
    print()
    print("  Para encerrar: feche esta janela")
    print("  ou pressione Ctrl+C")
    print("=" * 55)
    print()

    webbrowser.open(url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        try:
            ngrok.kill()
        except Exception:
            pass


if __name__ == '__main__':
    main()
