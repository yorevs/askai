from textwrap import dedent

from askai.core.component.scheduler import scheduler
from askai.core.component.text_streamer import streamer

if __name__ == '__main__':
    text_big = dedent("""
    # Classic Pancake Recipe

    ## Ingredients:
    - 1 cup all-purpose flour
    - 2 tablespoons sugar
    - 1 teaspoon baking powder
    - 1/2 teaspoon baking soda
    - 1/4 teaspoon salt
    - 1 cup buttermilk (or milk)
    - 1 large egg
    - 2 tablespoons melted butter (plus extra for the pan)
    - 1 teaspoon vanilla extract (optional)

    ## Instructions:

    1. **Mix dry ingredients**:
       In a large bowl, whisk together the flour, sugar, baking powder, baking soda, and salt.

    2. **Mix wet ingredients**:
       In a separate bowl, whisk together the buttermilk, egg, melted butter, and vanilla extract.

    3. **Combine**:
       Pour the wet ingredients into the dry ingredients and stir until just combined. The batter should be slightly lumpy, do not overmix.

    4. **Preheat and grease the pan**:
       Heat a non-stick skillet or griddle over medium heat. Lightly grease with butter.

    5. **Cook the pancakes**:
       For each pancake, pour about 1/4 cup of batter onto the pan. Cook until bubbles form on the surface and the edges appear set (about 2-3 minutes). Flip and cook the other side until golden brown.

    6. **Serve**:
       Serve the pancakes warm with your favorite toppings such as maple syrup, fresh fruits, or whipped cream.

    Enjoy your fluffy pancakes!

    """)
    text_small = "This is just a simple test to tell that PI is 3.14159265"
    scheduler.start()
    streamer.stream_text(text_small)
