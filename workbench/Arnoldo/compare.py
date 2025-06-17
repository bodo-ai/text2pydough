





dfA #reference
dfB 

# check rows are the same 
# check if the number of rows are the same
if dfA.shape[0] != dfB.shape[0]:
    return False


visited = set()
# iterate over the co lumns of dfA
for col in dfA.columns:
    for colB in dfB.columns:
        # check if the column names are similar
        if colB in visited:
            continue
        if match(dfA[col], dfB[colB]):
            visited.add(colB)
        else:
            return False
            
    return False
return true


def match(seriesA, seriesB, threshold = 0.00001, sorted=True):
    # check if the series are the same
    if seriesA.shape[0] != seriesB.shape[0]:
        return False
    # check if the series are the same
    
    if seriesA.dtype == seriesB.dtype:
        if seriesA.dtype == 'number':
            return abs(seriesA - seriesB).max() < threshold
        if seriesA.dtype == 'string':
            return seriesA.str.contains(seriesB).all()
        if seriesA.dtype == 'datetime': 
            return (seriesA - seriesB).dt.days.max() < 1
        if seriesA.dtype == 'boolean':  
            return (seriesA == seriesB).all()
   
    return True










