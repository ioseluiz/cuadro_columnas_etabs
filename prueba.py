from core.etabs import obtener_sapmodel_etabs, get_rectangular_concrete_sections
def main():
    sap_model = obtener_sapmodel_etabs()
    print(sap_model)
    
    numbers, materials, ret = sap_model.PropMaterial.GetNameList()
    print(numbers)
    print(materials)
    print(ret)

    num, names, ret = sap_model.PropFrame.GetNameList(0)
    print(num)
    print(names)
    print(ret)




if __name__ == "__main__":
    main()