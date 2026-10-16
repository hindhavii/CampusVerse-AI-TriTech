"""Create secrets for the local DEMO (do not commit the generated file)."""
from pathlib import Path
import secrets

root=Path(__file__).resolve().parent
cfg=root/'.streamlit'/'secrets.toml'
cfg.parent.mkdir(exist_ok=True)
if cfg.exists():
    print('Secrets are already configured at:',cfg)
    print('Existing credentials have NOT been replaced. Open the file locally to view them.')
else:
    vals={k:secrets.token_urlsafe(10) for k in ['ADMIN_PASSWORD','WORKER_PASSWORD','SECURITY_PASSWORD']}
    cfg.write_text(''.join(f'{k} = "{v}"\n' for k,v in vals.items()),encoding='utf-8')
    print('Local DEMO passwords created (save these securely; NEVER upload secrets.toml to GitHub):')
    for k,v in vals.items():print(f'  {k} : {v}')
    print('Set these same keys under Streamlit Cloud App Settings -> Secrets when deploying.')
