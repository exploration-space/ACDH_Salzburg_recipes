import recipe_utils

class XMLRecipe:
    def __init__(self, recipe:str, ingredients:list):
        self._features = recipe_utils.get_features(recipe)
        self.title = self._features['title']
        self._original_recipe = recipe_utils.get_recipe(recipe)
        self._annotated_recipe = recipe_utils.annotate_recipe(recipe, 
                                                              ingredients, 
                                                              matching=recipe_utils.fuzzy_match)
    
    def _create_xml(self, features_override:dict)->str:
        data = {}
        data.update(self._features)
        data.update(features_override)
        xml = recipe_utils.fill_recipe_template(data)
        return xml
    
    @property
    def original(self)->str:
        xml = self._create_xml({'recipe': self._original_recipe})
        xml = xml.replace('&lt;', '<').replace('&gt;', '>')
        return xml
    
    @property
    def annotated(self)->str:
        features_override = {
            'recipe': self._annotated_recipe,
            'ingredients': recipe_utils.get_ingredients(self._annotated_recipe)
        }
        
        xml = self._create_xml(features_override)
        xml = xml.replace('&lt;', '<').replace('&gt;', '>')
        
        return xml
    
    def __str__(self):
        return self.original

    def __repr__(self):
        return self.__str__()