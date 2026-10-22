"""GitHub App auth and read-only effective permission inspection.

Uses a securely supplied private key and the cryptography dependency at runtime.
Never logs credentials. Cannot grant permissions; it inspects actual installation grants.
"""
import json, os, time, urllib.request, urllib.error
BASE="https://api.github.com"
ACCEPT="application/vnd.github+json"

class GitHubAppError(RuntimeError): pass

def app_jwt(app_id,private_pem):
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError as exc:
        raise GitHubAppError("cryptography is required at runtime") from exc
    import base64
    def enc(data):
        return base64.urlsafe_b64encode(json.dumps(data,separators=(",",":")).encode()).rstrip(b"=").decode()
    now=int(time.time())
    body=enc({"iat":now-60,"exp":now+540,"iss":str(app_id)})
    head=enc({"alg":"RS256","typ":"JWT"})
    message=(head+"."+body).encode()
    key=serialization.load_pem_private_key(private_pem.encode(),password=None)
    signature=key.sign(message,padding.PKCS1v15(),hashes.SHA256())
    return head+"."+body+"."+base64.urlsafe_b64encode(signature).rstrip(b"=").decode()

def request(method,path,token):
    req=urllib.request.Request(BASE+path,headers={
        "Authorization":"Bearer "+token,"Accept":ACCEPT,"X-GitHub-Api-Version":"2022-11-28"
    },method=method)
    try:
        with urllib.request.urlopen(req,timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise GitHubAppError("GitHub request rejected (HTTP %d)"%exc.code) from None

def inspect_installation(app_id,private_key_pem,installation_id):
    jwt=app_jwt(app_id,private_key_pem)
    app=request("GET","/app",jwt)
    inst=request("GET","/app/installations/"+str(installation_id),jwt)
    account=inst.get("account") or {}
    return {"app_id":app.get("id"),"app_slug":app.get("slug"),
            "installation_id":inst.get("id"),"account_login":account.get("login"),
            "repository_selection":inst.get("repository_selection"),
            "effective_permissions":inst.get("permissions",{}),
            "repository_creation_write_attested":
               inst.get("permissions",{}).get("repository_creation")=="write"}

if __name__=="__main__":
    app_id=os.environ.get("UAES_GITHUB_APP_ID")
    key=os.environ.get("UAES_GITHUB_APP_PRIVATE_KEY_PEM")
    installation_id=os.environ.get("UAES_GITHUB_INSTALLATION_ID")
    if not (app_id and key and installation_id):
        print(json.dumps({"status":"BLOCKED","reason":"App ID, key or installation ID missing; no network call"}))
    else:
        print(json.dumps(inspect_installation(app_id,key,installation_id),indent=2,sort_keys=True))
