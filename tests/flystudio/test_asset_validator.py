from drosophila_pd.flystudio.asset_validator import AssetValidator
from drosophila_pd.flystudio.asset_database import AssetDatabase

def test_asset_validator():
    db = AssetDatabase()
    # Missing asset data
    db.register_asset("res1", None)

    validator = AssetValidator(database=db)
    errors = validator.validate()

    assert len(errors) == 1
    assert "Asset missing data: res1" in errors
