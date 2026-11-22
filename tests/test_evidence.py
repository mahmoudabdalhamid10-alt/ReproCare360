from repro360.evidence import KnowledgeBase, expand_query, stem, tokenize

kb = KnowledgeBase()


def test_knowledge_base_loads_33_entries():
    assert len(kb.entries) == 33
    assert {"id", "title", "text", "source"} <= set(kb.entries[0])


def test_stemmer():
    assert stem("running") == "runn"
    assert stem("babies") == "baby"
    assert stem("sperm") == "sperm"


def test_tokenize_strips_stopwords():
    assert "the" not in tokenize("the sperm and the heat")


def test_synonym_expansion():
    tokens = expand_query(tokenize("does weed reduce sperm count"), "does weed reduce sperm count")
    assert "cannabi" in tokens or "cannabis" in tokens


def test_search_returns_source_passages():
    res = kb.search("does weed reduce sperm count", k=2)
    assert not res["rejected"]
    assert res["results"][0]["id"] == "kb_cannabis"
    assert res["results"][0]["text"]


def test_search_rejects_unrelated():
    res = kb.search("how to change a car tire")
    assert res["rejected"] is True
    assert res["results"] == []


def test_empty_query_rejected():
    res = kb.search("???")
    assert res["rejected"] is True


def test_get_entry_by_id():
    assert kb.get("kb_smoking")["title"]
    assert kb.get("does_not_exist") is None
