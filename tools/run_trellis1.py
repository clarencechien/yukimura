"""Launch the ungated, original TRELLIS workflow with platform proxy and CA trust."""
def main():
    import truststore
    truststore.inject_into_ssl()
    import os,runpy,sys
    os.environ.setdefault('MODAL_SERVER_URL','https://api.modal.com')
    for upper,lower in [('MODAL_TOKEN_ID','modal_token_id'),('MODAL_TOKEN_SECRET','modal_token_secret')]:
        if not os.environ.get(upper) and os.environ.get(lower):os.environ[upper]=os.environ[lower]
    sys.argv=['modal','run','tools/trellis1_modal.py',*sys.argv[1:]]
    runpy.run_module('modal',run_name='__main__')
if __name__=='__main__':main()
