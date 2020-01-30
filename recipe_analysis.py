import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from tqdm import tqdm
import langdetect

import recipe_utils

def get_lengths_and_lang(recipes):
    df = pd.DataFrame(columns=['recipe', 'lang', 'length'])

    for recipe in tqdm(recipes):
        title = recipe_utils.get_recipe_title(recipe)
        tokens = recipe_utils.get_content_tokens(recipe)
        lang = langdetect.detect(' '.join(recipe_utils.get_content_tokens(recipe)))
        
        df.loc[len(df), :] = (title, lang, len(tokens))
    
    return df

def create_length_per_recipe_chart(length_per_recipe):
    sns.set(style="darkgrid")

    a4_dims = (15.7, 7.27)
    fig, ax = plt.subplots(figsize=a4_dims)

    return sns.distplot(length_per_recipe.loc[:,'length'], ax=ax, axlabel='Recipe content length')

def create_facet_grid(length_per_recipe):
    data = length_per_recipe.loc[length_per_recipe.lang.isin(['en', 'de']), :]
    sns.set(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})

    # Initialize the FacetGrid object
    pal = sns.cubehelix_palette(10, rot=-.25, light=.7)

    g = sns.FacetGrid(data=data, row="lang", hue="lang", aspect=15, height=1, palette=pal)

    # Draw the densities in a few steps
    g.map(sns.kdeplot, "length", clip_on=False, shade=True, alpha=1)
    g.map(sns.kdeplot, "length", clip_on=False, color="w")
    g.map(plt.axhline, y=0, lw=2, clip_on=False)


    # Define and use a simple function to label the plot in axes coordinates
    def label(x, color, label):
        ax = plt.gca()
        ax.text(0, .2, label, fontweight="bold", color=color,
                ha="left", va="center", transform=ax.transAxes)


    g.map(label, "length")

    # Set the subplots to overlap
    g.fig.subplots_adjust(hspace=-.25)

    # Remove axes details that don't play well with overlap
    g.set_titles("")
    g.set(yticks=[])
    g.despine(bottom=True, left=True)
    
    return g