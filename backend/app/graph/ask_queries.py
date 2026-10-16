"""Fixed read-only templates for company questions. No user-supplied Cypher."""

REVISION = "MATCH (m:Meta {key:'graph_revision'}) RETURN m.value AS revision"
ENTITIES = "MATCH (s:Service) RETURN s.id AS id,s.name AS name,s.aliases AS aliases ORDER BY s.id"
OWNERS = """MATCH (s:Service) WHERE s.id IN $ids
OPTIONAL MATCH (p:Person)-[o:OWNS {role:'primary'}]->(s)
RETURN s.id AS service_id,s.name AS service,p.id AS owner_id,p.name AS owner,o.claim_id AS claim_id
ORDER BY service_id,owner_id"""
DEPENDENTS = """MATCH p=(consumer:Service)-[:DEPENDS_ON*1..5]->(root:Service {id:$root_id})
RETURN consumer.id AS service_id,length(p) AS hops,[n IN nodes(p) | n.id] AS service_path,
[r IN relationships(p) | r.claim_id] AS claim_path ORDER BY hops,service_id"""
FRONTIER = """MATCH (s:Service)-[d:DEPENDS_ON]->(b:Service)
WHERE b.id IN $boundary AND NOT s.id IN $ids
RETURN DISTINCT s.id AS id,s.name AS name,d.claim_id AS claim_id ORDER BY name,id"""
PROJECTS = """MATCH (p:Project)-[u:USES]->(s:Service) WHERE s.id IN $ids
RETURN DISTINCT p.id AS project_id,p.name AS project,s.id AS service_id,u.claim_id AS claim_id
ORDER BY project_id,service_id"""
REVIEWERS = """MATCH (s:Service) WHERE s.id IN $ids
OPTIONAL MATCH (p:Person)-[o:OWNS {role:'primary'}]->(s)
OPTIONAL MATCH (p)-[m:MEMBER_OF]->(t:Team)
RETURN s.id AS service_id,s.name AS service,p.id AS owner_id,p.name AS owner,
o.claim_id AS claim_id,t.id AS team_id,t.name AS team,m.claim_id AS membership_claim_id
ORDER BY service_id,owner_id,team_id"""
DOCUMENTS = """CALL db.idx.fulltext.queryNodes('Source',$safe_query) YIELD node,score
WITH node,score WHERE node.kind = 'doc'
MATCH (r:SourceRevision) WHERE r.id = node.active_revision
RETURN node.id AS source_id,node.title AS title,r.body AS body,r.raw_text AS raw_text,
r.sha256 AS sha256,score AS ft_score ORDER BY ft_score DESC,source_id LIMIT 80"""
DESCRIPTIONS = """MATCH (doc:Source)-[d:DESCRIBES]->(s:Service) WHERE s.id IN $ids
RETURN d.claim_id AS claim_id ORDER BY claim_id"""
CITATIONS = """MATCH (c:Claim)-[:SUPPORTED_BY]->(r:SourceRevision) WHERE c.id IN $claim_ids
RETURN properties(c) AS claim,r.sha256 AS source_sha256,r.body AS source_body,
r.raw_text AS source_raw_text ORDER BY c.id"""

TEMPLATES = dict(owners=OWNERS, dependents=DEPENDENTS, projects=PROJECTS,
                 reviewers=REVIEWERS, documents=DOCUMENTS)
