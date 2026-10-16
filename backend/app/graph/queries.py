Q1 = """MATCH (d:Decision {id:$decision_id})-[c:CHANGES]->(s:Service)
RETURN d.id AS decision_id,d.status AS status,d.title AS title,d.created_at AS created_at,
d.proposed_supersedes_id AS old_id,d.obsolete_terms AS obsolete_terms,s.id AS root_id,c.claim_id AS claim_id ORDER BY root_id"""
Q2 = """MATCH p=(consumer:Service)-[:DEPENDS_ON*1..5]->(root:Service {id:$root_id})
RETURN consumer.id AS service_id,length(p) AS hops,[n IN nodes(p) | n.id] AS service_path,
[r IN relationships(p) | r.claim_id] AS claim_path ORDER BY hops,service_id"""
Q3 = """MATCH (p:Project)-[u:USES]->(s:Service) WHERE s.id IN $affected_ids
RETURN DISTINCT p.id AS project_id,p.name AS name,s.id AS via_service,u.claim_id AS claim_id ORDER BY project_id,via_service"""
Q4 = """MATCH (p:Person)-[o:OWNS]->(s:Service {id:$service_id})
RETURN p.id AS owner_id,p.name AS name,o.role AS role,o.claim_id AS claim_id ORDER BY owner_id"""
Q5 = """MATCH (c:Claim {id:$claim_id})-[:SUPPORTED_BY]->(r:SourceRevision)
RETURN properties(c) AS claim,r.source_id AS source_id,r.sha256 AS source_sha256,r.body AS source_body,r.raw_text AS source_raw_text"""
Q6 = """MATCH (s:Source)-[ref:REFERENCES]->(old:Decision {id:$old_id})
RETURN s.id AS source_id,s.kind AS kind,ref.claim_id AS claim_id ORDER BY source_id"""
Q7 = """CALL db.idx.fulltext.queryNodes('Source',$safe_query) YIELD node,score
RETURN node.id AS source_id,node.title AS title,node.kind AS kind,score AS ft_score ORDER BY ft_score DESC LIMIT 80"""
Q8 = """MATCH (doc:Source {kind:'doc'})-[d:DESCRIBES]->(s:Service) WHERE s.id IN $affected_ids
RETURN doc.id AS source_id,doc.last_reviewed_at AS last_reviewed_at,s.id AS service_id,d.claim_id AS claim_id ORDER BY source_id"""
