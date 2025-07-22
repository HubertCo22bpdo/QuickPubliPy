from docx import Document
import json
from fetchmeta import fetchmeta
import bib2json




class Bibliography:
    def __init__(self, identifier):
        self.word_file = Document()
        if type(identifier) == dict:
            self.bib = identifier
        if type(identifier) == str:
            with open(f'{identifier}', 'r') as f:
                self.bib = json.load(f)


    def insert(self, data, index=999999):
        if index > len(self.bib):

            self.bib[len(self.bib) + 1] = data
        else:
            for key in sorted(self.bib.keys(), reverse=True, key=int):
                key = int(key)
                if key >= index:
                    try:
                        self.bib[str(key + 1)] = self.bib.pop(str(key))
                    except:
                        try:
                            self.bib[key + 1] = self.bib.pop(key)
                        except e as e:
                            print(e, '\nActual indexing error')

            self.bib[index] = data
        self.bib = dict(sorted(self.bib.items(), key=lambda dictbib: int(dictbib[0])))

    def insert_from_doi(self, doi, index=999999):
        data = fetchmeta(f'{doi}')
        # with open(fr'.\_temp.bib', 'w') as f:
        #     f.write(fetchmeta(f'{doi}', 'bibtex'))
        # bib2json.convert_file(".\_temp.bib", ".\_temp.json")
        # with open(fr'.\_temp.json', 'r') as f:
        #     data = json.load(f)
        authors_str = ''
        for author in data['author']:
            authors_str += author['given'] + ' ' + author['family'] + ', '

        if 'page' in data.keys():
            if '-' in data['page']:
                pages = data['page'].split('-')
            else:
                pages = data['page']
        else:
            input_pages = input('Pages not found, input here (for range use format: 999-999):')
            if '-' in input_pages:
                pages = input_pages.split('-')
            else:
                pages = input_pages
        
        formated_data = {
            'Autors': authors_str[:-2],
            'DOI': doi,
            'Year': data['published']['date-parts'][0][0],
            'Pages': pages,
            'Journal': data['container-title'],
            'Title': data['title'],
            'Volume': data['volume'],
            'Issue': data['issue'] if 'issue'in data.keys() else None
        }
        self.insert(formated_data, index=index)
        
    def remove(self, index):
        try:
            del self.bib[str(index)]
        except:
            del self.bib[int(index)]
        for key in sorted(self.bib.keys(), key=int):
            key = int(key)
            if key >= index:
                try:
                    self.bib[str(key - 1)] = self.bib.pop(str(key))
                except:
                    try:
                        self.bib[key - 1] = self.bib.pop(key)
                    except e as e:
                        print(e, '\nActual indexing error')

        self.bib = dict(sorted(self.bib.items(), key=lambda dictbib: int(dictbib[0])))

    def export_bibliography(self, style, filename='defult_bib.docx'):
        for nr, info_dict in self.bib.items():
            if style == 'Chicago':
                citation = self.word_file.add_paragraph(f'{nr}.\t')

                # Autors' names are parsed here
                names_str = ''
                full_names = info_dict["Autors"].split(',')
                if len(full_names) > 6:
                    count_names = True
                    counter = 0
                else:
                    count_names = False
                for full_name in full_names:
                    name_list = full_name.split(' ')
                    while '' in name_list:
                        name_list.remove('')
                    skip = -1
                    special_specifier = ''
                    if name_list[-1] in ['Jr.', 'Jr', 'Sr.', 'Sr' 'I', 'II', 'III', 'IV', 'V']:
                        special_specifier = name_list[-1]
                        name_list = name_list[:-1]
                    try:
                        if name_list[-3][0].islower() and name_list[-2][0].islower():
                            last_name =  name_list[-3] +' '+ name_list[-2] +' '+ name_list[-1] + special_specifier
                            skip = -3
                    except:
                        continue
                    if name_list[-2][0].islower() and (skip != -3):
                        last_name =  name_list[-2] +' '+ name_list[-1] + special_specifier
                        skip = -2
                    elif skip == -1:  
                        last_name = name_list[-1] + special_specifier
                    if count_names:
                        counter += 1
                        if counter == 4:
                            names_str += f'et al., '
                            break
                    for name in name_list[:skip]:
                        if '-' in name:
                            parts = name.split('-')
                            name = f'{parts[0][0]}.'
                            for part in parts[1:]:
                                if part[0].isupper():
                                    name += f'-{part[0]}.'
                        else:
                            name = f'{name[0]}.'
                        names_str += f'{name} '
                    names_str += f'{last_name}, '
                citation.add_run(names_str)

                #Title
                citation.add_run('"')
                title = info_dict["Title"]
                format_stack = []
                i = 0
                while i < len(title):
                    if title.startswith(r'\textit{', i):
                        format_stack.append('italic')
                        i += len(r'\textit{')
                    elif title.startswith(r'\textbf{', i):
                        format_stack.append('bold')
                        i += len(r'\textbf{')
                    elif title.startswith('^{', i):
                        format_stack.append('superscript')
                        i += 2
                    elif title.startswith('_{', i):
                        format_stack.append('subscript')
                        i += 2
                    elif title.startswith('}\\', i):
                        if format_stack:
                            format_stack.pop()
                        i += 2
                    else:
                        run = citation.add_run(title[i])
                        run.font.italic = 'italic' in format_stack
                        run.font.bold = 'bold' in format_stack
                        run.font.superscript = 'superscript' in format_stack
                        run.font.subscript = 'subscript' in format_stack
                        i += 1
                citation.add_run('" ')

                #Journal name
                citation.add_run(f'{info_dict["Journal"]} ').italic = True

                #Year
                citation.add_run(f'{info_dict["Year"]}').bold = True
                citation.add_run(f', ')

                #Volume
                citation.add_run(f'{info_dict["Volume"]}').italic = True
                citation.add_run(f', ')

                #Issue
                if info_dict["Issue"] is not None:
                    citation.add_run(f'{info_dict["Issue"]}, ')
                
                #Pages
                if type(info_dict["Pages"]) == tuple or type(info_dict["Pages"]) == list:
                    citation.add_run(f'{info_dict["Pages"][0]},')
                else:
                    citation.add_run(f'{info_dict["Pages"]},')

                #DOI
                self.word_file.add_paragraph(f'DOI: {info_dict["DOI"]}')

                self.word_file.save(filename)

    def save_json(self, filename):
        with open(f'{filename}.json', 'w') as f:
            json.dump(self.bib, f, indent=2)