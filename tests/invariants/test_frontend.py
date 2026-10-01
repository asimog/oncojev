"""Phase 8: the frontend is presentation-only with distinct epistemic categories."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"

FRONTEND_SOURCES = tuple((WEB / "app").rglob("*.tsx")) + tuple((WEB / "lib").rglob("*.ts"))

FORBIDDEN_BACKEND_TOKENS = (
    "admit_scientific_evidence",
    "FrontierPolicy",
    "run_cycle",
    "ScienceExecutor",
    "src.persistence",
    "src.science",
    "src.runtime",
)


def test_frontend_contains_no_orchestration_or_scientific_logic():
    for path in FRONTEND_SOURCES:
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_BACKEND_TOKENS:
            assert token not in text, f"{token} leaked into {path.relative_to(ROOT)}"


def test_frontend_distinguishes_all_epistemic_categories():
    categories = (WEB / "lib/categories.ts").read_text(encoding="utf-8")
    styles = (WEB / "app/globals.css").read_text(encoding="utf-8")
    for category in ("observation", "measurement", "evidence", "jev", "hypothesis", "action"):
        assert f"{category}:" in categories
        assert f".cat-{category}" in styles
        assert f".badge-{category}" in styles


def test_generated_snapshot_never_admits_synthetic_rows():
    from scripts.export_snapshot import build_snapshot
    data=build_snapshot()
    assert data["overview"]["evidence"]==0
    assert data["data_provenance"]=="synthetic_fixture" and data["conditions"]==[]
    assert data["transport"]=="offline_snapshot"
    measurements=data["blocks"][0]["reconstruction"]["measurements"]
    assert measurements and all(m["origin"]=="synthetic" for m in measurements)
    assert data["blocks"][0]["reconstruction"]["dossier"]["evidence_refs"]==[]


def test_rendered_live_and_fallback_views_preserve_provenance_and_failure():
    import shutil,subprocess
    import pytest
    if shutil.which("node") is None or not (WEB/"node_modules/typescript").exists():
        pytest.skip("existing web development environment required; no dependencies installed by test")
    script=r"""
const fs=require('fs'),path=require('path'),Module=require('module'),assert=require('assert');
const ts=require('typescript');
const resolve=Module._resolveFilename;
Module._resolveFilename=function(name,parent,...args){return resolve.call(this,name.startsWith('@/')?path.resolve(name.slice(2)):name,parent,...args)};
for(const extension of ['.ts','.tsx'])require.extensions[extension]=(module,file)=>module._compile(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true,target:ts.ScriptTarget.ES2022}}).outputText,file);
const fixture=JSON.parse(fs.readFileSync('data/snapshot.json','utf8'));
const block=structuredClone(fixture.blocks[0]);
block.reconstruction.block.status='failed';block.reconstruction.run_outcome='failed';block.reconstruction.complete=false;
block.reconstruction.outcome_inferred=true;block.reconstruction.dossier.objective_attainment='unknown';
block.reconstruction.dossier.operational_failures=[{error_type:'SourceTimeout'}];
const overview={...fixture.overview,latest_cycle:{mode:'live',status:'failed',error_type:'SourceTimeout'},data_provenance:'retained_records',source_activity:{attempts:3,successes:1,failures:1,unresolved:1}};
global.fetch=async(url,options)=>{
 assert.equal(options.cache,'no-store');
 const body=url.endsWith('/api/overview')?overview:url.endsWith('/api/blocks')?{blocks:[block.summary]}:url.endsWith('/api/research-memory')?{research_memory:[]}:block.reconstruction;
 return new Response(JSON.stringify(body),{status:200});
};
(async()=>{
 const {getData}=require('./lib/snapshot.ts');
 const data=await getData();assert.equal(data.transport,'live_api');assert.deepEqual(data.conditions,[]);assert.equal(data.data_provenance,'retained_records');
 const render=require('react-dom/server').renderToStaticMarkup;
 const page=require('./app/page.tsx').default;
 const html=render(await page());assert(html.includes('live_api')&&html.includes('retained_records')&&html.includes('SourceTimeout'));
 assert(html.includes('Source attempts 3')&&html.includes('successes 1')&&html.includes('failures 1'));
 const detail=render(await require('./app/blocks/[blockId]/page.tsx').default({params:{blockId:block.summary.block_id}}));
 assert(detail.includes('historical completion claim contradicted or unverified')&&detail.includes('SourceTimeout')&&detail.includes('objective attainment unknown'));
 global.fetch=async()=>{throw new Error('offline')};
 const offline=await getData();assert.equal(offline.transport,'offline_snapshot');assert.equal(offline.data_provenance,'synthetic_fixture');assert.equal(offline.overview.evidence,0);
 const fallback=render(await page());assert(fallback.includes('offline_snapshot')&&fallback.includes('synthetic_fixture')&&fallback.includes('Live API unavailable'));
 console.log('rendered live/fallback provenance, failures, source counters and objective uncertainty passed');
})().catch(error=>{console.error(error);process.exit(1)});
"""
    result=subprocess.run(["node","-"],input=script,cwd=WEB,capture_output=True,text=True,timeout=30)
    assert result.returncode==0, result.stdout+result.stderr
