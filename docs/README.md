# LUX MED Group API Client
Work in progress towards the most complete LUX MED Group patient portal API client.  
Because your health data belongs to you :)

## Installation
To install, simply use `pip`:

```bash
pip install -e git://github.com/przemal/luxmed#egg=luxmed
```

## Basic usage
```python
from luxmed import LuxMed

luxmed = LuxMed(user_name='user', password='pass')

# user profile data
print(luxmed.user())

# cities the service is available in
print(', '.join(luxmed.cities().values()))
```
For full usage please refer to the source code for now.
