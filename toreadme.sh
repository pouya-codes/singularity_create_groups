echo """# Create Groups


### Development Information ###

\`\`\`
Date Created: 22 July 2020
Last Update: 26 July 2021 by Amirali
Developer: Colin Chen
Version: 1.3
\`\`\`

**Before running any experiment to be sure you are using the latest commits of all modules run the following script:**
\`\`\`
(cd /projects/ovcare/classification/singularity_modules ; ./update_modules.sh --bcgsc-pass your/bcgsc/path)
\`\`\`

## Usage

\`\`\`""" > README.md

python app.py -h >> README.md
echo >> README.md
python app.py from-experiment-manifest -h >> README.md
echo >> README.md
python app.py from-arguments -h >> README.md
echo >> README.md
python app.py from-arguments use-extracted-patches -h >> README.md
echo >> README.md
python app.py from-arguments use-extracted-patches use-manifest -h >> README.md
echo >> README.md
python app.py from-arguments use-extracted-patches use-origin -h >> README.md
echo >> README.md
python app.py from-arguments use-hd5 -h >> README.md
echo >> README.md
python app.py from-arguments use-hd5 use-manifest -h >> README.md
echo >> README.md
python app.py from-arguments use-hd5 use-origin -h >> README.md
echo >> README.md
echo """\`\`\`
TODO: there is a chance --balance_patches sets empty groups. This happens if any patches for some (group, category) is zero.
TODO: in create_groups, variables are named 'subtype' instead of 'category'. That leads to confusion.
TODO: further explain how --max_patient_patches works in description.
TODO: make GroupCreator.group_summary() return DataFrame. Test against DataFrame output.
""" >> README.md
