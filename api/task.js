// Vercel Node.js function: a bounded, stateless agent task runner.
// Public deployment MUST enable Vercel Authentication or equivalent access control.
const roles = {
  general: "You are a pragmatic personal assistant. Be specific and do not claim to perform actions you did not perform.",
  research: "You are a skeptical research analyst. Search when available, cite source URLs, distinguish facts and uncertainty.",
  proactive: "You are a proactive project strategist. Identify concrete next steps, risks and priorities. Do not execute external actions."
};
const limits = new Map();
function json(res,status,data){res.status(status).setHeader("Cache-Control","no-store");res.json(data);}
export default async function handler(req,res){
  if(req.method!=="POST") return json(res,405,{error:"Method not allowed"});
  // The dashboard must be protected by Vercel Authentication.
  if(process.env.VERCEL_ENV==="production" && process.env.AGENT_ENABLE_PRODUCTION!=="true")
    return json(res,403,{error:"Production task execution disabled until explicit enablement."});
  const origin=req.headers.origin;
  const host=req.headers.host;
  if(origin){try{if(new URL(origin).host!==host)return json(res,403,{error:"Origin denied"});}catch{return json(res,403,{error:"Invalid origin"});}}
  const ip=(req.headers["x-forwarded-for"]||"").split(",")[0].slice(0,80)||"unknown";
  const minute=Math.floor(Date.now()/60000);
  const info=limits.get(ip);
  if(info?.minute===minute && info.count>=4)return json(res,429,{error:"Rate limit reached"});
  limits.set(ip,{minute,count:info?.minute===minute?info.count+1:1});
  if(limits.size>1000)limits.clear();
  const role=req.body?.role;
  const goal=String(req.body?.goal||"").trim();
  if(!Object.hasOwn(roles,role)||goal.length<3||goal.length>4000)return json(res,400,{error:"Invalid role or goal"});
  const key=process.env.OPENAI_API_KEY||process.env.opaenai_api_key;
  if(!key)return json(res,503,{error:"OpenAI API key is not configured for this deployment."});
  const payload={model:process.env.OPENAI_MODEL||"gpt-6.1-sol",instructions:roles[role],input:goal,max_output_tokens:1200,store:false};
  if(role==="research")payload.tools=[{type:"web_search"}];
  try{
    const abort=new AbortController();const timeout=setTimeout(()=>abort.abort(),50000);
    let api;
    try{api=await fetch("https://api.openai.com/v1/responses",{method:"POST",headers:{"Authorization":"Bearer "+key,"Content-Type":"application/json"},body:JSON.stringify(payload),signal:abort.signal});}
    finally{clearTimeout(timeout);}
    const body=await api.json();
    if(!api.ok)return json(res,502,{error:"Model request failed",providerStatus:api.status});
    const text=(body.output||[]).flatMap(x=>(x.content||[]).filter(c=>c.type==="output_text").map(c=>c.text||"")).join("\n");
    if(!text)return json(res,502,{error:"Model returned no text"});
    return json(res,200,{role,result:text,usage:{input_tokens:body.usage?.input_tokens||0,output_tokens:body.usage?.output_tokens||0},timestamp:new Date().toISOString()});
  }catch(e){return json(res,502,{error:e.name==="AbortError"?"Request timed out":"Model request unavailable"});}
}
