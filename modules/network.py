from core.models import Tweak
from core.diagnostics import run_command

def flush():
 code,out,err=run_command("Clear-DnsClientCache")
 if code: raise RuntimeError(err or out or "DNS cache clear failed.")
 return "DNS client cache cleared."
def scan(): return [Tweak("flush_dns","Flush DNS cache","Network","Maintenance action; does not change your DNS provider.","SAFE",False,False,False,"None",None,flush)]
