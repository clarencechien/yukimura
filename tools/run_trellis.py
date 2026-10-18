"""Launch TRELLIS Modal jobs with existing system trust and environment credentials."""
def main():
    import truststore
    truststore.inject_into_ssl()
    import os, runpy, sys
    os.environ.setdefault('MODAL_SERVER_URL', 'https://api.modal.com')
    for upper, lower in [('MODAL_TOKEN_ID', 'modal_token_id'), ('MODAL_TOKEN_SECRET', 'modal_token_secret')]:
        if not os.environ.get(upper) and os.environ.get(lower):
            os.environ[upper] = os.environ[lower]
    if '--build-only' in sys.argv:
        os.environ['TRELLIS_ENVIRONMENT_CHECK_ONLY'] = '1'
    else:
        import modal
        name = os.environ.get('TRELLIS_HF_SECRET', 'trellis-huggingface')
        if not any(secret.name == name for secret in modal.Secret.objects.list()):
            raise SystemExit(
                f'Missing Modal Secret {name!r}. In Modal, create it with HF_TOKEN from an account '
                'approved for facebook/dinov3-vitl16-pretrain-lvd1689m. '
                'No GPU job was started. See docs/experiments/future-sanada/README.md.'
            )
    sys.argv = ['modal', 'run', 'tools/trellis_modal.py', *sys.argv[1:]]
    runpy.run_module('modal', run_name='__main__')

if __name__ == '__main__':
    main()
