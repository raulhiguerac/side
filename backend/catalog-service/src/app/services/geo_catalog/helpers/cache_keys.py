def cache_key_localities(*, country: str) -> str:                                                             
    return f"catalog:{country}:localities"                                                                 
                                                                                                            
def cache_key_locality(*, locality_id: str) -> str:                                                           
    return f"catalog:locality:{locality_id}"                                                               
                                                                                                            
def cache_key_neighborhoods(*, locality_id: str) -> str:
    return f"catalog:locality:{locality_id}:neighborhoods"

def cache_key_neighborhood(*, neighborhood_id: str) -> str:
    return f"catalog:neighborhood:{neighborhood_id}"