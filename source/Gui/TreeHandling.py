# -*- coding: utf-8 -*-
"""
This class is intended to deal with the drawing (.dxf) structure. It has the following functions:
- populate the entities treeView and the layers treeView
- allow selection of shapes from any treeView and show the selection on the graphic view
- allow to enable/disable shapes from any treeView
- reflects into the treeView the changes that occurs on the graphic view
- set export order using drag & drop
@newfield purpose: Purpose
@newfield sideeffect: Side effect, Side effects

@purpose: display tree structure of the .dxf file, select, enable and set export order of the shapes
@author: Xavier Izard
@since:  2012.10.01
@license: GPL
"""

from PyQt4 import QtCore, QtGui
from Gui.myTreeView import MyStandardItemModel
from math import degrees

import Core.Globals as g

from Core.CustomGCode import CustomGCodeClass

import logging
logger=logging.getLogger("Gui.TreeHandling") 

#defines some arbitrary types for the objects stored into the treeView.
#These types will eg help us to find which kind of data is stored in the element received from a click() event
ENTITY_OBJECT = QtCore.Qt.UserRole + 1 #For storing refs to the entities elements (entities_list)
LAYER_OBJECT = QtCore.Qt.UserRole + 2  #For storing refs to the layers elements (layers_list)
SHAPE_OBJECT = QtCore.Qt.UserRole + 3  #For storing refs to the shape elements (entities_list & layers_list)
CUSTOM_GCODE_OBJECT = QtCore.Qt.UserRole + 4  #For storing refs to the custom gcode elements (layers_list)

SELECTION_COL = 1 #Column that is selectable in the treeViews
PATH_OPTIMISATION_COL = 3 #Column that corresponds to TSP enable checkbox



class TreeHandler(QtGui.QWidget):
    """
    Class to handle both QTreeView :  entitiesTreeView (for blocks, and the tree of blocks) and layersShapesTreeView (for layers and shapes)
    """

    def __init__(self, ui):
        """
        Standard method to initialize the class
        @param ui: the QT4 GUI
        """
        QtGui.QWidget.__init__(self)
        self.ui = ui

        #Used to store previous values in order to enable/disable text
        self.palette = self.ui.zRetractionArealLineEdit.palette()
        self.clearToolsParameters()

        #Layers & Shapes TreeView
        self.layer_item_model = None
        self.layers_list = None
        self.auto_update_export_order = False
        self.ui.layersShapesTreeView.setSelectionCallback(self.actionOnSelectionChange) #pass the callback function to the QTreeView
        self.ui.layersShapesTreeView.setKeyPressEventCallback(self.actionOnKeyPress)
        self.ui.layersShapesTreeView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.ui.layersShapesTreeView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        QtCore.QObject.connect(self.ui.layersGoUpPushButton, QtCore.SIGNAL("clicked()"), self.ui.layersShapesTreeView.moveUpCurrentItem)
        QtCore.QObject.connect(self.ui.layersGoDownPushButton, QtCore.SIGNAL("clicked()"), self.ui.layersShapesTreeView.moveDownCurrentItem)

        #Load the tools from the config file to the tool selection combobox
        for tool in g.config.vars.Tool_Parameters:
            self.ui.toolDiameterComboBox.addItem(tool)

        #Select the first tool in the list and update the tools diameter, ... accordingly
        self.ui.toolDiameterComboBox.setCurrentIndex(0)
        self.toolUpdate(self.ui.toolDiameterComboBox.currentText())

        QtCore.QObject.connect(self.ui.toolDiameterComboBox, QtCore.SIGNAL("activated(const QString &)"), self.toolUpdate)
        QtCore.QObject.connect(self.ui.zRetractionArealLineEdit, QtCore.SIGNAL("textEdited(const QString &)"), self.toolParameterzRetractionArealUpdate)
        QtCore.QObject.connect(self.ui.zSafetyMarginLineEdit, QtCore.SIGNAL("textEdited(const QString &)"), self.toolParameterzSafetyMarginUpdate)
        QtCore.QObject.connect(self.ui.zInfeedDepthLineEdit, QtCore.SIGNAL("textEdited(const QString &)"), self.toolParameterzInfeedDepthUpdate)
        QtCore.QObject.connect(self.ui.zInitialMillDepthLineEdit, QtCore.SIGNAL("textEdited(const QString &)"), self.toolParameterzInitialMillDepthUpdate)
        QtCore.QObject.connect(self.ui.zFinalMillDepthLineEdit, QtCore.SIGNAL("textEdited(const QString &)"), self.toolParameterzFinalMillDepthUpdate)
        QtCore.QObject.connect(self.ui.g1FeedXYLineEdit, QtCore.SIGNAL("textEdited(const QString &)"), self.toolParameterg1FeedXYUpdate)
        QtCore.QObject.connect(self.ui.g1FeedZLineEdit, QtCore.SIGNAL("textEdited(const QString &)"), self.toolParameterg1FeedZUpdate)

        #Entities TreeView
        self.entity_item_model = None
        self.entities_list = None
        self.ui.entitiesTreeView.setSelectionCallback(self.actionOnSelectionChange) #pass the callback function to the QTreeView
        self.ui.entitiesTreeView.setKeyPressEventCallback(self.actionOnKeyPress)
        self.ui.entitiesTreeView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.ui.entitiesTreeView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        QtCore.QObject.connect(self.ui.blocksCollapsePushButton, QtCore.SIGNAL("clicked()"), self.expandToDepth0)
        QtCore.QObject.connect(self.ui.blocksExpandPushButton, QtCore.SIGNAL("clicked()"), self.ui.entitiesTreeView.expandAll)

        #Build the contextual menu (mouse right click)
        self.context_menu = QtGui.QMenu(self)

        menu_action = self.context_menu.addAction("Unselect all")
        menu_action.triggered.connect(self.ui.layersShapesTreeView.clearSelection)

        menu_action = self.context_menu.addAction("Select all")
        menu_action.triggered.connect(self.ui.layersShapesTreeView.selectAll)

        self.context_menu.addSeparator()

        menu_action = self.context_menu.addAction("Disable selection")
        menu_action.triggered.connect(self.disableSelectedItems)

        menu_action = self.context_menu.addAction("Enable selection")
        menu_action.triggered.connect(self.enableSelectedItems)

        self.context_menu.addSeparator()

        menu_action = self.context_menu.addAction("Don't opti. route for selection")
        menu_action.triggered.connect(self.doNotOptimizeRouteForSelectedItems)

        menu_action = self.context_menu.addAction("Optimize route for selection")
        menu_action.triggered.connect(self.optimizeRouteForSelectedItems)

        self.context_menu.addSeparator()

        menu_action = self.context_menu.addAction("Remove custom GCode")
        menu_action.triggered.connect(self.removeCustomGCode)

        sub_menu = QtGui.QMenu("Add custom GCode ...", self)
        for custom_action in g.config.vars.Custom_Actions:
            menu_action = sub_menu.addAction(QtCore.QString(custom_action).replace('_', ' '))
            menu_action.setData(custom_action) #save the exact name of the action, as it is defined in the config file. We will use it later to identify the action

        self.context_menu.addMenu(sub_menu)

        #Right click menu
        self.ui.layersShapesTreeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        QtCore.QObject.connect(self.ui.layersShapesTreeView, QtCore.SIGNAL("customContextMenuRequested(const QPoint &)"), self.displayContextMenu)

        #Not used for now, so hide them
        self.ui.startAtXLabel.hide()
        self.ui.startAtYLabel.hide()
        self.ui.startAtXLineEdit.hide()
        self.ui.startAtYLineEdit.hide()



    def displayContextMenu(self, position):
        """
        Slot used to display a right click context menu
        @param position: position of the cursor within the treeView widget
        """
        selected_action = self.context_menu.exec_(self.ui.layersShapesTreeView.mapToGlobal(position))

        if selected_action and selected_action.data().isValid():
            #contextual menu selection concerns a custom gcode
            custom_gcode_name = selected_action.data().toString()

            self.addCustomGCodeAfter(custom_gcode_name)



    def expandToDepth0(self):
        """
        Slot used to expand the entities treeView up to depth 0
        """
        self.ui.entitiesTreeView.expandToDepth(0)



    def buildLayerTree(self, layers_list):
        """
        This method populates the Layers QTreeView with all the elements contained into the layers_list
        Method must be called each time a new .dxf file is loaded. 
        options
        @param layers_list: list of the layers and shapes (created in the main)
        """
        self.layers_list = layers_list
        if self.layer_item_model:
            self.layer_item_model.clear() #Remove any existing item_model
        self.layer_item_model = MyStandardItemModel() #This is the model view (QStandardItemModel). it's the container for the data
        self.layer_item_model.setSupportedDragActions(QtCore.Qt.MoveAction)
        self.layer_item_model.setHorizontalHeaderItem(0, QtGui.QStandardItem("[en]"));
        self.layer_item_model.setHorizontalHeaderItem(1, QtGui.QStandardItem("Name"));
        self.layer_item_model.setHorizontalHeaderItem(2, QtGui.QStandardItem("Nbr"));
        self.layer_item_model.setHorizontalHeaderItem(3, QtGui.QStandardItem("Opti.\npath"));
        modele_root_element = self.layer_item_model.invisibleRootItem() #Root element of our tree

        for layer in layers_list:
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/images/layer.png"))
            checkbox_element = QtGui.QStandardItem(icon, "")
            checkbox_element.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable)
            checkbox_element.setData(QtCore.QVariant(layer), LAYER_OBJECT) #store a ref to the layer in our treeView element - this is a method to map tree elements with real data
            checkbox_element.setCheckState(QtCore.Qt.Checked)

            modele_element = QtGui.QStandardItem(layer.LayerName)
            modele_element.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

            nbr_element = QtGui.QStandardItem()
            nbr_element.setFlags(QtCore.Qt.ItemIsEnabled)
            optimise_element = QtGui.QStandardItem()
            optimise_element.setFlags(QtCore.Qt.ItemIsEnabled)

            modele_root_element.appendRow([checkbox_element, modele_element, nbr_element, optimise_element])

            for shape in layer.shapes:
                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(":/images/shape.png"))
                item_col_0 = QtGui.QStandardItem(icon, "") #will only display a checkbox + an icon that will never be disabled
                item_col_0.setData(QtCore.QVariant(shape), SHAPE_OBJECT) #store a ref to the shape in our treeView element
                item_col_0.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable)

                item_col_1 = QtGui.QStandardItem(shape.type)
                item_col_1.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

                item_col_2 = QtGui.QStandardItem(str(shape.nr))
                item_col_2.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled)

                item_col_3 = QtGui.QStandardItem()
                item_col_3.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)

                parent_item = modele_root_element.child(modele_root_element.rowCount() - 1, 0)
                parent_item.appendRow([item_col_0, item_col_1, item_col_2, item_col_3])

                #Deal with the checkboxes (shape enabled or disabled / send shape to TSP optimizer)
                item_col_0.setCheckState(QtCore.Qt.Unchecked if shape.isDisabled() else QtCore.Qt.Checked)
                item_col_3.setCheckState(QtCore.Qt.Checked if shape.isToolPathOptimized() else QtCore.Qt.Unchecked)

        #Signal to get events when a checkbox state changes (enable or disable shapes)
        QtCore.QObject.connect(self.layer_item_model, QtCore.SIGNAL("itemChanged(QStandardItem*)"), self.on_itemChanged)

        self.ui.layersShapesTreeView.setModel(self.layer_item_model) #Affect our model to the GUI TreeView, in order to display it

        self.ui.layersShapesTreeView.expandAll()

        self.ui.layersShapesTreeView.setDragDropMode(QtGui.QTreeView.InternalMove)
        #self.ui.layersShapesTreeView.setDefaultDropAction(QtCore.Qt.MoveAction)
        #self.ui.layersShapesTreeView.setDragDropOverwriteMode(True)
        self.ui.layersShapesTreeView.setDropIndicatorShown(True)
        self.ui.layersShapesTreeView.setAcceptDrops(True)
        self.ui.layersShapesTreeView.setDragEnabled(True)

        self.ui.layersShapesTreeView.resizeColumnToContents(3)
        self.ui.layersShapesTreeView.resizeColumnToContents(2)
        self.ui.layersShapesTreeView.resizeColumnToContents(1)
        self.ui.layersShapesTreeView.resizeColumnToContents(0)



    def buildEntitiesTree(self, entities_list):
        """
        This method populates the Entities (blocks) QTreeView with all the elements contained in the entities_list
        Method must be called each time a new .dxf file is loaded. 
        options
        @param entities_list: list of the layers and shapes (created in the main)
        """

        self.entities_list = entities_list
        if self.entity_item_model:
            self.entity_item_model.clear() #Remove any existing item_model
        self.entity_item_model = QtGui.QStandardItemModel()
        self.entity_item_model.setHorizontalHeaderItem(0, QtGui.QStandardItem("[en]"));
        self.entity_item_model.setHorizontalHeaderItem(1, QtGui.QStandardItem("Name"));
        self.entity_item_model.setHorizontalHeaderItem(2, QtGui.QStandardItem("Nr"));
        self.entity_item_model.setHorizontalHeaderItem(3, QtGui.QStandardItem("Type"));
        self.entity_item_model.setHorizontalHeaderItem(4, QtGui.QStandardItem("Base point"));
        self.entity_item_model.setHorizontalHeaderItem(5, QtGui.QStandardItem("Scale"));
        self.entity_item_model.setHorizontalHeaderItem(6, QtGui.QStandardItem("Rotation"));
        modele_root_element = self.entity_item_model.invisibleRootItem()

        self.buildEntitiesSubTree(modele_root_element, entities_list)

        #Signal to get events when a checkbox state changes (enable or disable shapes)
        QtCore.QObject.connect(self.entity_item_model, QtCore.SIGNAL("itemChanged(QStandardItem*)"), self.on_itemChanged)

        self.ui.entitiesTreeView.setModel(self.entity_item_model)

        self.ui.entitiesTreeView.expandToDepth(0)

        i = 0
        while(i < 6):
            self.ui.entitiesTreeView.resizeColumnToContents(i)
            i += 1



    def buildEntitiesSubTree(self, elements_model, elements_list):
        """
        This method is called (possibly recursively) to populate the
        Entities treeView. It is not intended to be called directly,
        use buildEntitiesTree() function instead.
        options
        @param elements_model: the treeView model (used to store the data, see QT docs)
        @param elements_list: either a list of entities, or a shape
        """
        if isinstance(elements_list, list):
            #We got a list
            for element in elements_list:
                self.addEntitySubTree(elements_model, element)

        else:
            #Unique element (shape)
            element = elements_list
            self.addEntitySubTree(elements_model, element)



    def addEntitySubTree(self, elements_model, element):
        """
        This method populates a row of the Entities treeView. It is
        not intended to be called directly, use buildEntitiesTree()
        function instead.
        options
        @param elements_model: the treeView model (used to store the data, see QT docs)
        @param element: the Entity or Shape element
        """
        item_col_0 = None
        if element.type == "Entitie":
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/images/blocks.png"))
            item_col_0 = QtGui.QStandardItem(icon, "") #will only display a checkbox + an icon that will never be disabled
            item_col_0.setData(QtCore.QVariant(element), ENTITY_OBJECT) #store a ref to the entity in our treeView element

            item_col_1 = QtGui.QStandardItem(element.Name)
            item_col_2 = QtGui.QStandardItem(str(element.Nr))
            item_col_3 = QtGui.QStandardItem(element.type)

            item_col_4 = QtGui.QStandardItem(str(element.p0))
            item_col_4.setFlags(QtCore.Qt.ItemIsEnabled)

            item_col_5 = QtGui.QStandardItem(str(element.sca))
            item_col_5.setFlags(QtCore.Qt.ItemIsEnabled)

            item_col_6 = QtGui.QStandardItem(str(round(degrees(element.rot), 3))) #convert the angle into degrees with 3 digit after the decimal point
            item_col_6.setFlags(QtCore.Qt.ItemIsEnabled)

            elements_model.appendRow([item_col_0, item_col_1, item_col_2, item_col_3, item_col_4, item_col_5, item_col_6])

            for sub_element in element.children:
                self.buildEntitiesSubTree(item_col_0, sub_element)

        elif element.type == "Shape":
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/images/shape.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            item_col_0 = QtGui.QStandardItem(icon, "") #will only display a checkbox + an icon that will never be disabled
            item_col_0.setData(QtCore.QVariant(element), SHAPE_OBJECT) #store a ref to the entity in our treeView element

            item_col_1 = QtGui.QStandardItem(element.type)
            item_col_2 = QtGui.QStandardItem(str(element.nr))
            item_col_3 = QtGui.QStandardItem(element.type)

            elements_model.appendRow([item_col_0, item_col_1, item_col_2, item_col_3])

        item_col_0.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable)
        item_col_1.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        item_col_2.setFlags(QtCore.Qt.ItemIsEnabled)
        item_col_3.setFlags(QtCore.Qt.ItemIsEnabled)

        #Deal with the checkbox (everything is enabled at start)
        item_col_0.setCheckState(QtCore.Qt.Checked)



    def updateExportOrder(self):
        """
        Update the layers_list order to reflect the TreeView order.
        This function must be called before generating the GCode
        (export function). Export will be performed in the order of the
        structure self.LayerContents of the main. Each layer contains
        some shapes, and the export order of the shapes is set by
        populating the exp_order[] list with the shapes reference number
        for each layer (eg exp_order = [5, 3, 2, 4, 0, 1] for layer 0,
        exp_order = [5, 3, 7] for layer 1, ...)
        options
        """

        i = self.layer_item_model.rowCount(QtCore.QModelIndex())
        while i > 0:
            i -= 1
            layer_item_index = self.layer_item_model.index(i, 0)

            if layer_item_index.data(LAYER_OBJECT).isValid():
                real_layer = layer_item_index.data(LAYER_OBJECT).toPyObject()
                self.layers_list.remove(real_layer)    #Remove the layer from its original position
                self.layers_list.insert(0, real_layer) #and insert it at the beginning of the layer's list

                real_layer.exp_order = [] #Clear the current export order
                real_layer.exp_order_complete = [] #Clear the current export order

                #Assign the export order for the shapes of the layer "real_layer"
                j = 0
                while j < self.layer_item_model.rowCount(layer_item_index):
                    shape_item_index = self.layer_item_model.index(j, 0, layer_item_index)

                    real_shape = None
                    if shape_item_index.data(SHAPE_OBJECT).isValid():
                        real_shape = shape_item_index.data(SHAPE_OBJECT).toPyObject()
                        if real_shape.isDisabled() is False:
                            real_layer.exp_order.append(real_shape.nr) #Create the export order list with the real and unique shapes numbers (eg [25, 22, 30, 4, 1, 5])

                    if shape_item_index.data(CUSTOM_GCODE_OBJECT).isValid():
                        real_shape = shape_item_index.data(CUSTOM_GCODE_OBJECT).toPyObject()

                    if real_shape and real_shape.isDisabled() is False:
                        real_layer.exp_order_complete.append(real_layer.shapes.index(real_shape)) #Create the export order list with the shapes & custom gcode numbers (eg [5, 3, 2, 4, 0, 1])

                    j += 1



    def updateTreeViewOrder(self):
        """
        Update the Layer TreeView order according to the exp_order list
        of each layer. This function should be called after running the
        TSP path otimizer
        """

        i = self.layer_item_model.rowCount(QtCore.QModelIndex())
        while i > 0:
            i -= 1
            layer_item_index = self.layer_item_model.index(i, 0)
            layer_item = self.layer_item_model.itemFromIndex(layer_item_index)

            if layer_item_index.data(LAYER_OBJECT).isValid():
                real_layer = layer_item_index.data(LAYER_OBJECT).toPyObject()

                #for shape_nr in real_layer.exp_order[::-1]: #reverse order and prepend if we want to insert optimized shape before fixed shapes
                for shape_nr in real_layer.exp_order:
                    j = 0
                    while j < self.layer_item_model.rowCount(layer_item_index):
                        shape_item_index = self.layer_item_model.index(j, 0, layer_item_index)

                        real_shape = None
                        if shape_item_index.data(SHAPE_OBJECT).isValid():
                            real_shape = shape_item_index.data(SHAPE_OBJECT).toPyObject()

                            if real_shape and real_shape.nr == shape_nr and (real_shape.send_to_TSP or g.config.vars.Route_Optimisation['TSP_shape_order'] == 'CONSTRAIN_ORDER_ONLY'):
                                #Shape number "shape_nr" found in the treeView and Shape is movable => moving it to its new position
                                item_to_be_moved = layer_item.takeRow(j)
                                layer_item.appendRow(item_to_be_moved)

                                break

                        j += 1



    def updateShapeSelection(self, shape, select):
        """
        This method is a "slot" (callback) called from the main when the
        selection changes on the graphic view. It aims to update the
        treeView selection according to the graphic view.
        Note: in order to avoid signal loops, all selection signals are
        blocked when updating the selections in the treeViews
        options
        @param shape: the Shape whose selection has changed
        @param selection: whether the Shape has been selected (True) or unselected (False)
        """

        #Layer treeView
        item_index = self.findLayerItemIndexFromShape(shape)
        selection_model = self.ui.layersShapesTreeView.selectionModel() #Get the selection model of the QTreeView

        if item_index:
            #we found the matching index for the shape in our layers treeView model
            self.ui.layersShapesTreeView.blockSignals(True) #Avoid signal loops (we dont want the treeView to re-emit selectionChanged signal)
            if select:
                #Select the matching shape in the list. We select column 0 and SELECTION_COL column (ie item name)
                selection_model.select(item_index.sibling(item_index.row(), SELECTION_COL), QtGui.QItemSelectionModel.Select)
                selection_model.select(item_index, QtGui.QItemSelectionModel.Select)
            else:
                #Unselect the matching shape in the list. We deselect column 0 and SELECTION_COL column (ie item name)
                selection_model.select(item_index.sibling(item_index.row(), SELECTION_COL), QtGui.QItemSelectionModel.Deselect)
                selection_model.select(item_index, QtGui.QItemSelectionModel.Deselect)
            self.ui.layersShapesTreeView.blockSignals(False)

        #Entities treeView
        item_index = self.findEntityItemIndexFromShape(shape)
        selection_model = self.ui.entitiesTreeView.selectionModel() #Get the selection model of the QTreeView

        if item_index:
            #we found the matching index for the shape in our entities treeView model
            self.ui.entitiesTreeView.blockSignals(True) #Avoid signal loops (we dont want the treeView to re-emit selectionChanged signal)
            if select:
                #Select the matching shape in the list. We select column 0 and SELECTION_COL column (ie item type)
                selection_model.select(item_index.sibling(item_index.row(), SELECTION_COL), QtGui.QItemSelectionModel.Select)
                selection_model.select(item_index, QtGui.QItemSelectionModel.Select)
            else:
                #Unselect the matching shape in the list. We deselect column 0 and SELECTION_COL column (ie item type)
                selection_model.select(item_index.sibling(item_index.row(), SELECTION_COL), QtGui.QItemSelectionModel.Deselect)
                selection_model.select(item_index, QtGui.QItemSelectionModel.Deselect)
            self.ui.entitiesTreeView.blockSignals(False)

        #Update the tool parameters fields
        self.clearToolsParameters()
        self.displayToolParametersForItem(shape.LayerContent, shape)



    def updateShapeEnabling(self, shape, enable):
        """
        This method is a "slot" (callback) called from the main when the
        shapes are enabled or disabled on the graphic view.
        It aims to update the treeView checkboxes according to the
        graphic view.
        Note: in order to avoid signal loops, all selection signals are
        blocked when updating the checkboxes in the treeViews
        options
        @param shape: the Shape whose enabling has changed
        @param enable: whether the Shape has been enabled (True) or disabled (False)
        """
        #Layer treeView
        item_index = self.findLayerItemIndexFromShape(shape)

        if item_index:
            #we found the matching index for the shape in our treeView model
            item = item_index.model().itemFromIndex(item_index)

            self.layer_item_model.blockSignals(True) #Avoid signal loops (we dont want the treeView to emit itemChanged signal)
            if enable:
                #Select the matching shape in the list
                self.updateCheckboxOfItem(item, QtCore.Qt.Checked)

            else:
                #Unselect the matching shape in the list
                self.updateCheckboxOfItem(item, QtCore.Qt.Unchecked)

            self.layer_item_model.blockSignals(False)
            self.ui.layersShapesTreeView.update(item_index) #update the treeList drawing
            self.traverseParentsAndUpdateEnableDisable(self.layer_item_model, item_index) #update the parents checkboxes

            if self.auto_update_export_order:
                #update export order and thus export drawing
                self.prepareExportOrderUpdate()


        #Entities treeView
        item_index = self.findEntityItemIndexFromShape(shape)

        if item_index:
            #we found the matching index for the shape in our treeView model
            item = item_index.model().itemFromIndex(item_index)

            self.entity_item_model.blockSignals(True) #Avoid signal loops (we dont want the treeView to emit itemChanged signal)
            if enable:
                #Select the matching shape in the list
                self.updateCheckboxOfItem(item, QtCore.Qt.Checked)

            else:
                #Unselect the matching shape in the list
                self.updateCheckboxOfItem(item, QtCore.Qt.Unchecked)

            self.entity_item_model.blockSignals(False)
            self.ui.entitiesTreeView.update(item_index) #update the treeList drawing
            self.traverseParentsAndUpdateEnableDisable(self.entity_item_model, item_index) #update the parents checkboxes



    def findLayerItemIndexFromShape(self, shape):
        """
        Find internal layers treeView reference (item index) matching a
        "real" shape (ie a ShapeClass instance)
        options
        @param shape: the real shape (ShapeClass instance)
        @return: the found item index
        """
        return self.traverseChildrenAndFindShape(self.layer_item_model, QtCore.QModelIndex(), shape); #Return the item found (can be None)

    def findEntityItemIndexFromShape(self, shape):
        """
        Find internal entities treeView reference (item index) matching
        a "real" shape (ie a ShapeClass instance)
        options
        @param shape: the real shape (ShapeClass instance)
        @return: the found item index
        """
        return self.traverseChildrenAndFindShape(self.entity_item_model, QtCore.QModelIndex(), shape); #Return the item found (can be None)

    def traverseChildrenAndFindShape(self, item_model, item_index, shape):
        """
        This method is used by the findLayerItemIndexFromShape() and
        findEntityItemIndexFromShape() function in order to find a
        reference from a layer. It traverses the QT model and compares
        each item data with the shape passed as parameter. When found,
        the reference is returned
        options
        @param item_model: the treeView model (used to store the data, see QT docs)
        @param item_index: the initial model index (QModelIndex) in the tree (all children of this index are scanned)
        @param shape: the real shape (ShapeClass instance)
        @return: the found item index
        """
        found_item_index = None

        i = 0
        while i < item_model.rowCount(item_index):
            sub_item_index = item_model.index(i, 0, item_index)

            if sub_item_index.data(SHAPE_OBJECT).isValid():
                real_item = sub_item_index.data(SHAPE_OBJECT).toPyObject()
                if shape == real_item:
                    return sub_item_index

            if item_model.hasChildren(sub_item_index):
                found_item_index = self.traverseChildrenAndFindShape(item_model, sub_item_index, shape);
                if found_item_index:
                    return found_item_index

            i += 1



    def traverseChildrenAndSelect(self, selection_model, item_model, item_index, select):
        """
        This method is used internally to select/unselect all children
        of a given entity (eg to select all the shapes of a given layer
        when the user has selected a layer)
        options
        @param item_model: the treeView model (used to store the data, see QT docs)
        @param item_index: the initial model index (QModelIndex) in the tree (all children of this index are scanned)
        @param select: whether to select (True) or not (False)
        """

        i = 0
        while i < item_model.rowCount(item_index):
            sub_item_index = item_model.index(i, 0, item_index)

            if item_model.hasChildren(sub_item_index):
                self.traverseChildrenAndSelect(selection_model, item_model, sub_item_index, select);

            element = sub_item_index.model().itemFromIndex(sub_item_index)
            if element:
                if element.data(SHAPE_OBJECT).isValid() or element.data(CUSTOM_GCODE_OBJECT).isValid():
                    #only select Shapes or Custom GCode
                    col_item_index = sub_item_index.sibling(sub_item_index.row(), SELECTION_COL) #Get the only column that is selectable (eg item name)
                    selection_model.select(col_item_index, QtGui.QItemSelectionModel.Select if select else QtGui.QItemSelectionModel.Deselect)

            i += 1



    def traverseChildrenAndEnableDisable(self, item_model, item_index, checked_state):
        """
        This method is used internally to check/uncheck all children of
        a given entity (eg to enable all shapes of a given layer when
        the user has enabled a layer)
        options
        @param item_model: the treeView model (used to store the data, see QT docs)
        @param item_index: the initial model index (QModelIndex) in the tree (all children of this index are scanned)
        @param checked_state: the state of the checkbox
        """

        i = 0
        while i < item_model.rowCount(item_index):
            sub_item_index = item_model.index(i, 0, item_index)

            if item_model.hasChildren(sub_item_index):
                self.traverseChildrenAndEnableDisable(item_model, sub_item_index, checked_state);

            item = item_model.itemFromIndex(sub_item_index)
            if item:
                self.updateCheckboxOfItem(item, checked_state)

            i += 1


    def traverseParentsAndUpdateEnableDisable(self, item_model, item_index):
        """
        This code updates the parents checkboxes for a given entity.
        Parents checkboxes are tristate, eg if some of the shapes that
        belong to a layer are checked and others not, then the checkbox
        of this layer will be "half" checked
        options
        @param item_model: the treeView model (used to store the data, see QT docs)
        @param item_index: the initial model index (QModelIndex) in the tree (all children of this index are scanned)
        """
        has_unchecked = False
        has_partially_checked = False
        has_checked = False
        item = None
        parent_item_index = None
        i = 0
        while i < item_model.rowCount(item_index.parent()):
            parent_item_index = item_model.index(i, 0, item_index.parent())

            item = item_model.itemFromIndex(parent_item_index)
            if item:
                if item.checkState() == QtCore.Qt.Checked:
                    has_checked = True
                elif item.checkState() == QtCore.Qt.PartiallyChecked:
                    has_partially_checked = True
                else:
                    has_unchecked = True

            i += 1

        #Update the parent item according to its children
        if item and item.parent():
            parent_state = item.parent().checkState()
            if has_checked and has_unchecked or has_partially_checked:
                parent_state = QtCore.Qt.PartiallyChecked
            elif has_checked and not has_unchecked:
                parent_state = QtCore.Qt.Checked
            elif not has_checked and has_unchecked:
                parent_state = QtCore.Qt.Unchecked

            self.updateCheckboxOfItem(item.parent(), parent_state)

        #Handle the parent of the parent (recursive call)
        if parent_item_index and parent_item_index.parent().isValid():
            self.traverseParentsAndUpdateEnableDisable(item_model, parent_item_index.parent());



    def toolUpdate(self, text):
        """
        Slot that updates the tool's diameter, speed and start_radius
        when a new tool is selected
        @param text: the name of the newly selected tool
        """

        if not text.isEmpty():
            new_diameter = g.config.vars.Tool_Parameters[str(text)]['diameter']
            new_speed = g.config.vars.Tool_Parameters[str(text)]['speed']
            new_start_radius = g.config.vars.Tool_Parameters[str(text)]['start_radius']

            self.ui.toolDiameterComboBox.setPalette(self.palette)
            self.ui.toolDiameterLabel.setText(str(round(new_diameter, 3)))
            self.ui.toolDiameterLabel.setPalette(self.palette) #Restore color
            self.ui.toolSpeedLabel.setText(str(round(new_speed, 1)))
            self.ui.toolSpeedLabel.setPalette(self.palette) #Restore color
            self.ui.startRadiusLabel.setText(str(round(new_start_radius, 3)))
            self.ui.startRadiusLabel.setPalette(self.palette) #Restore color

            #Get the new value and convert it to int
            val = text.toInt()
            if val[1]:
                selected_indexes_list = self.ui.layersShapesTreeView.selectedIndexes();
    
                for model_index in selected_indexes_list:
                    if model_index.isValid():
                        model_index = model_index.sibling(model_index.row(), 0) #get the first column of the selected row, since it's the only one that contains data
                        element = model_index.model().itemFromIndex(model_index)
                        real_item = None
                        if element.data(SHAPE_OBJECT).isValid():
                            real_item = element.data(SHAPE_OBJECT).toPyObject().LayerContent #Shape has no such property => update the parent layer
                        elif element and element.data(LAYER_OBJECT).isValid():
                            real_item = element.data(LAYER_OBJECT).toPyObject()
                        if not real_item is None:
                            real_item.tool_nr = val[0]
                            real_item.tool_diameter = new_diameter
                            real_item.speed = new_speed
                            real_item.start_radius = new_start_radius
                            self.tool_nr = real_item.tool_nr
                            self.tool_diameter = new_diameter
                            self.speed = new_speed
                            self.start_radius = new_start_radius



    def toolParameterzRetractionArealUpdate(self, text):
        """
        Slot that updates the above tools parameter when the
        corresponding LineEdit changes
        @param text: the value of the LineEdit
        """
        self.ui.zRetractionArealLineEdit.setPalette(self.palette) #Restore color

        #Get the new value and convert it to float
        val = text.toFloat()
        if val[1]:
            selected_indexes_list = self.ui.layersShapesTreeView.selectedIndexes();

            for model_index in selected_indexes_list:
                if model_index.isValid():
                    model_index = model_index.sibling(model_index.row(), 0) #get the first column of the selected row, since it's the only one that contains data
                    element = model_index.model().itemFromIndex(model_index)
                    real_item = None
                    if element.data(SHAPE_OBJECT).isValid():
                        real_item = element.data(SHAPE_OBJECT).toPyObject().LayerContent #Shape has no such property => update the parent layer
                    elif element and element.data(LAYER_OBJECT).isValid():
                        real_item = element.data(LAYER_OBJECT).toPyObject()
                    if not real_item is None:
                        real_item.axis3_retract = val[0]
                        self.axis3_retract = real_item.axis3_retract



    def toolParameterzSafetyMarginUpdate(self, text):
        """
        Slot that updates the above tools parameter when the
        corresponding LineEdit changes
        @param text: the value of the LineEdit
        """
        self.ui.zSafetyMarginLineEdit.setPalette(self.palette) #Restore color

        #Get the new value and convert it to float
        val = text.toFloat()
        if val[1]:
            selected_indexes_list = self.ui.layersShapesTreeView.selectedIndexes();

            for model_index in selected_indexes_list:
                if model_index.isValid():
                    model_index = model_index.sibling(model_index.row(), 0) #get the first column of the selected row, since it's the only one that contains data
                    element = model_index.model().itemFromIndex(model_index)
                    real_item = None
                    if element.data(SHAPE_OBJECT).isValid():
                        real_item = element.data(SHAPE_OBJECT).toPyObject().LayerContent
                    elif element and element.data(LAYER_OBJECT).isValid():
                        real_item = element.data(LAYER_OBJECT).toPyObject()
                    if not real_item is None:
                        real_item.axis3_safe_margin = val[0]
                        self.axis3_safe_margin = real_item.axis3_safe_margin



    def toolParameterzInfeedDepthUpdate(self, text):
        """
        Slot that updates the above tools parameter when the
        corresponding LineEdit changes
        @param text: the value of the LineEdit
        """
        self.ui.zInfeedDepthLineEdit.setPalette(self.palette) #Restore color

        #Get the new value and convert it to float
        val = text.toFloat()
        if val[1]:
            selected_indexes_list = self.ui.layersShapesTreeView.selectedIndexes();

            for model_index in selected_indexes_list:
                if model_index.isValid():
                    model_index = model_index.sibling(model_index.row(), 0) #get the first column of the selected row, since it's the only one that contains data
                    element = model_index.model().itemFromIndex(model_index)
                    real_item = None
                    if element.data(SHAPE_OBJECT).isValid():
                        real_item = element.data(SHAPE_OBJECT).toPyObject()
                    elif element and element.data(LAYER_OBJECT).isValid():
                        real_item = element.data(LAYER_OBJECT).toPyObject()
                    if not real_item is None:
                        real_item.axis3_slice_depth = val[0]
                        self.axis3_slice_depth = real_item.axis3_slice_depth



    def toolParameterg1FeedXYUpdate(self, text):
        """
        Slot that updates the above tools parameter when the
        corresponding LineEdit changes
        @param text: the value of the LineEdit
        """
        self.ui.g1FeedXYLineEdit.setPalette(self.palette) #Restore color

        #Get the new value and convert it to float
        val = text.toFloat()
        if val[1]:
            selected_indexes_list = self.ui.layersShapesTreeView.selectedIndexes();

            for model_index in selected_indexes_list:
                if model_index.isValid():
                    model_index = model_index.sibling(model_index.row(), 0) #get the first column of the selected row, since it's the only one that contains data
                    element = model_index.model().itemFromIndex(model_index)
                    real_item = None
                    if element.data(SHAPE_OBJECT).isValid():
                        real_item = element.data(SHAPE_OBJECT).toPyObject()
                    elif element and element.data(LAYER_OBJECT).isValid():
                        real_item = element.data(LAYER_OBJECT).toPyObject()
                    if not real_item is None:
                        real_item.f_g1_plane = val[0]
                        self.f_g1_plane = real_item.f_g1_plane



    def toolParameterg1FeedZUpdate(self, text):
        """
        Slot that updates the above tools parameter when the
        corresponding LineEdit changes
        @param text: the value of the LineEdit
        """
        self.ui.g1FeedZLineEdit.setPalette(self.palette) #Restore color

        #Get the new value and convert it to float
        val = text.toFloat()
        if val[1]:
            selected_indexes_list = self.ui.layersShapesTreeView.selectedIndexes();

            for model_index in selected_indexes_list:
                if model_index.isValid():
                    model_index = model_index.sibling(model_index.row(), 0) #get the first column of the selected row, since it's the only one that contains data
                    element = model_index.model().itemFromIndex(model_index)
                    real_item = None
                    if element.data(SHAPE_OBJECT).isValid():
                        real_item = element.data(SHAPE_OBJECT).toPyObject()
                    elif element and element.data(LAYER_OBJECT).isValid():
                        real_item = element.data(LAYER_OBJECT).toPyObject()
                    if not real_item is None:
                        real_item.f_g1_depth = val[0]
                        self.f_g1_depth = real_item.f_g1_depth



    def toolParameterzInitialMillDepthUpdate(self, text):
        """
        Slot that updates the above tools parameter when the
        corresponding LineEdit changes
        @param text: the value of the LineEdit
        """
        self.ui.zInitialMillDepthLineEdit.setPalette(self.palette) #Restore color

        #Get the new value and convert it to float
        val = text.toFloat()
        if val[1]:
            selected_indexes_list = self.ui.layersShapesTreeView.selectedIndexes();

            for model_index in selected_indexes_list:
                if model_index.isValid():
                    model_index = model_index.sibling(model_index.row(), 0) #get the first column of the selected row, since it's the only one that contains data
                    element = model_index.model().itemFromIndex(model_index)
                    real_item = None
                    if element.data(SHAPE_OBJECT).isValid():
                        real_item = element.data(SHAPE_OBJECT).toPyObject()
                    elif element and element.data(LAYER_OBJECT).isValid():
                        real_item = element.data(LAYER_OBJECT).toPyObject()
                    if not real_item is None:
                        real_item.axis3_start_mill_depth = val[0]
                        self.axis3_start_mill_depth = real_item.axis3_start_mill_depth



    def toolParameterzFinalMillDepthUpdate(self, text):
        """
        Slot that updates the above tools parameter when the
        corresponding LineEdit changes
        @param text: the value of the LineEdit
        """
        self.ui.zFinalMillDepthLineEdit.setPalette(self.palette) #Restore color

        #Get the new value and convert it to float
        val = text.toFloat()
        if val[1]:
            selected_indexes_list = self.ui.layersShapesTreeView.selectedIndexes();

            for model_index in selected_indexes_list:
                if model_index.isValid():
                    model_index = model_index.sibling(model_index.row(), 0) #get the first column of the selected row, since it's the only one that contains data
                    element = model_index.model().itemFromIndex(model_index)
                    real_item = None
                    if element.data(SHAPE_OBJECT).isValid():
                        real_item = element.data(SHAPE_OBJECT).toPyObject()
                    elif element and element.data(LAYER_OBJECT).isValid():
                        real_item = element.data(LAYER_OBJECT).toPyObject()
                    if not real_item is None:
                        real_item.axis3_mill_depth = val[0]
                        self.axis3_mill_depth = real_item.axis3_mill_depth



    def actionOnSelectionChange(self, parent, selected, deselected):
        """
        This function is a callback called from QTreeView class when
        something changed in the selection. It aims to update the
        graphic view according to the tree selection. It also deals
        with children selection when a parent is selected
        Note that there is no predefined signal for
        selectionChange event, that's why we use a callback function
        options
        @param parent: QT parent item (unused)
        @param select: list of selected items in the treeView
        @param deselect: list of deselected items in the treeView
        """
        self.clearToolsParameters() #disable tools parameters widgets, ...

        #Deselects all the shapes that are selected
        for selection in deselected:
            for model_index in selection.indexes():
                if model_index.isValid():
                    model_index = model_index.sibling(model_index.row(), 0) #get the first column of the selected row, since it's the only one that contains data
                    element = model_index.model().itemFromIndex(model_index)
                    if element:
                        if element.data(SHAPE_OBJECT).isValid():
                            self.updateTreeViewSelection(model_index, element, False) #Effectively unselect the shape
                            """ Disabled for now, because it's not really user friendly
                        elif element.data(LAYER_OBJECT).isValid():
                            self.traverseChildrenAndSelect(self.ui.layersShapesTreeView.selectionModel(), self.layer_item_model, model_index, False)
                        """
                        elif element.data(ENTITY_OBJECT).isValid():
                            self.traverseChildrenAndSelect(self.ui.entitiesTreeView.selectionModel(), self.entity_item_model, model_index, False)


        #Selects all the shapes that are selected
        for selection in selected:
            for model_index in selection.indexes():
                if model_index.isValid():
                    model_index = model_index.sibling(model_index.row(), 0) #get the first column of the selected row, since it's the only one that contains data
                    element = model_index.model().itemFromIndex(model_index)
                    if element:
                        if element.data(SHAPE_OBJECT).isValid():
                            real_item = element.data(SHAPE_OBJECT).toPyObject()
                            #update the tools parameters according to the selection
                            self.displayToolParametersForItem(real_item.LayerContent, real_item)

                            self.updateTreeViewSelection(model_index, element, True) #Effectively select the shape

                        elif element.data(LAYER_OBJECT).isValid():
                            real_item = element.data(LAYER_OBJECT).toPyObject()
                            #select all the child of a given layer when clicked. Code disabled for now, because it's not really user friendly
                            #self.traverseChildrenAndSelect(self.ui.layersShapesTreeView.selectionModel(), self.layer_item_model, model_index, True)

                            #update the tools parameters according to the selection
                            self.displayToolParametersForItem(real_item)

                        #select all the child of a given entity when clicked. Code disabled for now, because it's not really user friendly
                        elif element.data(ENTITY_OBJECT).isValid():
                            self.traverseChildrenAndSelect(self.ui.entitiesTreeView.selectionModel(), self.entity_item_model, model_index, True)



    def clearToolsParameters(self):
        """
        This function restore defaults for tools parameters widgets
        (disabled, default color, ...)
        """
        number_of_selected_items = len(self.ui.layersShapesTreeView.selectedIndexes())

        if number_of_selected_items <= 2: #2 selections = 1 row of 2 columns
            # 0 or 1 row are selected => clear some states
            self.tool_nr = None
            self.tool_diameter = None
            self.speed = None
            self.start_radius = None
            self.axis3_retract = None
            self.axis3_safe_margin = None
            self.axis3_slice_depth = None
            self.axis3_start_mill_depth = None
            self.axis3_mill_depth = None
            self.f_g1_plane = None
            self.f_g1_depth = None

            self.ui.toolDiameterComboBox.setPalette(self.palette)
            self.ui.toolDiameterLabel.setPalette(self.palette)
            self.ui.toolSpeedLabel.setPalette(self.palette)
            self.ui.startRadiusLabel.setPalette(self.palette)
            self.ui.zRetractionArealLineEdit.setPalette(self.palette)
            self.ui.zSafetyMarginLineEdit.setPalette(self.palette)
            self.ui.zInfeedDepthLineEdit.setPalette(self.palette)
            self.ui.g1FeedXYLineEdit.setPalette(self.palette)
            self.ui.g1FeedZLineEdit.setPalette(self.palette)
            self.ui.zInitialMillDepthLineEdit.setPalette(self.palette)
            self.ui.zFinalMillDepthLineEdit.setPalette(self.palette)


        if number_of_selected_items == 0:
            self.ui.millSettingsFrame.setEnabled(False)

        else:
            self.ui.millSettingsFrame.setEnabled(True)



    def displayToolParametersForItem(self, layer_item, shape_item = None):
        """
        Display the current tools settings (fill the QLineEdit, ...)
        for the Layer / Shape passed as parameter
        @param layer_item: layer instance as defined in LayerContent.py
        @param shape_item: shape instance as defined in Shape.py
        """
        #Selects the tool for the selected layer
        self.ui.toolDiameterComboBox.setCurrentIndex(self.ui.toolDiameterComboBox.findText(str(layer_item.tool_nr)))
        if not self.tool_nr is None and layer_item.tool_nr != self.tool_nr:
            #Several different tools are currently selected => grey background for the combobox
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Button, QtCore.Qt.gray)
            self.ui.toolDiameterComboBox.setPalette(palette)
        self.tool_nr = layer_item.tool_nr

        self.tool_diameter = self.updateAndColorizeWidget(self.ui.toolDiameterLabel, self.tool_diameter, layer_item.tool_diameter)

        self.speed = self.updateAndColorizeWidget(self.ui.toolSpeedLabel, self.speed, layer_item.speed)

        self.start_radius = self.updateAndColorizeWidget(self.ui.startRadiusLabel, self.start_radius, layer_item.start_radius)

        self.axis3_retract = self.updateAndColorizeWidget(self.ui.zRetractionArealLineEdit, self.axis3_retract, layer_item.axis3_retract)

        self.axis3_safe_margin = self.updateAndColorizeWidget(self.ui.zSafetyMarginLineEdit, self.axis3_safe_margin, layer_item.axis3_safe_margin)

        if shape_item and shape_item.axis3_slice_depth is not None:
            #If Shape slice_depth is defined, then use it instead of the one of the layer
            self.axis3_slice_depth = self.updateAndColorizeWidget(self.ui.zInfeedDepthLineEdit, self.axis3_slice_depth, shape_item.axis3_slice_depth)
        else:
            self.axis3_slice_depth = self.updateAndColorizeWidget(self.ui.zInfeedDepthLineEdit, self.axis3_slice_depth, layer_item.axis3_slice_depth)

        if shape_item and shape_item.axis3_start_mill_depth is not None:
            #If Shape initial mill_depth is defined, then use it instead of the one of the layer
            self.axis3_start_mill_depth = self.updateAndColorizeWidget(self.ui.zInitialMillDepthLineEdit, self.axis3_start_mill_depth, shape_item.axis3_start_mill_depth)
        else:
            self.axis3_start_mill_depth = self.updateAndColorizeWidget(self.ui.zInitialMillDepthLineEdit, self.axis3_start_mill_depth, layer_item.axis3_start_mill_depth)

        if shape_item and shape_item.axis3_mill_depth is not None:
            #If Shape mill_depth is defined, then use it instead of the one of the layer
            self.axis3_mill_depth = self.updateAndColorizeWidget(self.ui.zFinalMillDepthLineEdit, self.axis3_mill_depth, shape_item.axis3_mill_depth)
        else:
            self.axis3_mill_depth = self.updateAndColorizeWidget(self.ui.zFinalMillDepthLineEdit, self.axis3_mill_depth, layer_item.axis3_mill_depth)

        if shape_item and shape_item.f_g1_plane is not None:
            #If Shape XY speed is defined, then use it instead of the one of the layer
            self.f_g1_plane = self.updateAndColorizeWidget(self.ui.g1FeedXYLineEdit, self.f_g1_plane, shape_item.f_g1_plane)
        else:
            self.f_g1_plane = self.updateAndColorizeWidget(self.ui.g1FeedXYLineEdit, self.f_g1_plane, layer_item.f_g1_plane)

        if shape_item and shape_item.f_g1_depth is not None:
            #If Shape Z speed is defined, then use it instead of the one of the layer
            self.f_g1_depth = self.updateAndColorizeWidget(self.ui.g1FeedZLineEdit, self.f_g1_depth, shape_item.f_g1_depth)
        else:
            self.f_g1_depth = self.updateAndColorizeWidget(self.ui.g1FeedZLineEdit, self.f_g1_depth, layer_item.f_g1_depth)



    def updateAndColorizeWidget(self, widget, previous_value, value):
        """
        This function colours the text in grey when two values are
        different. It is used to show differences in tools settings
        when several layers / shapes are selected.
        @param widget: QT widget to update (can be a QLabel or a QLineEdit)
        @param previous_value: the value of the previously selected item
        @param value: the value (parameter) of the selected item
        """
        widget.setText(str(round(value, 4))) #Round the value with at most 4 digits

        if previous_value != None and value != previous_value:
            #Several different tools parameter are currently selected (eg: mill deph = -3 for the first selected item and -2 for the second) => grey color for the text
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Text, QtCore.Qt.gray)
            widget.setPalette(palette)

        return value



    def updateTreeViewSelection(self, model_index, element, select):
        """
        Really update the shape selection on the graphic view. Also
        selects the matching shapes in the treeView counterpart
        (layers treeView -> entities treeView and vice versa)
        @param model_index: the treeView model (used to store the data, see QT docs)
        @param element: the real shape (ShapeClass instance)
        @param select: whether to select (True) or not (False)
        """
        real_item = element.data(SHAPE_OBJECT).toPyObject()
        real_item.setSelected(select, True) #Select the shape on the canvas and ask to don't propagate events in order to avoid events loops

        #Update the other TreeViews
        item_index = self.findEntityItemIndexFromShape(real_item)
        if model_index.model() == self.layer_item_model and item_index:
            item_index = item_index.sibling(item_index.row(), SELECTION_COL) #Get the only column that is selectable (ie item type)
            self.ui.entitiesTreeView.blockSignals(True) #Avoid signal loops (we dont want the treeView to re-emit selectionChanged signal)
            selection_model = self.ui.entitiesTreeView.selectionModel()
            selection_model.select(item_index, QtGui.QItemSelectionModel.Select if select else QtGui.QItemSelectionModel.Deselect)
            self.ui.entitiesTreeView.blockSignals(False)

        item_index = self.findLayerItemIndexFromShape(real_item)
        if model_index.model() == self.entity_item_model and item_index:
            item_index = item_index.sibling(item_index.row(), SELECTION_COL) #Get the only column that is selectable (ie item name)
            self.ui.layersShapesTreeView.blockSignals(True) #Avoid signal loops (we dont want the treeView to re-emit selectionChanged signal)
            selection_model = self.ui.layersShapesTreeView.selectionModel()
            selection_model.select(item_index, QtGui.QItemSelectionModel.Select if select else QtGui.QItemSelectionModel.Deselect)
            self.ui.layersShapesTreeView.blockSignals(False)


    def disableSelectedItems(self):
        selected_indexes_list = self.ui.layersShapesTreeView.selectedIndexes();

        for model_index in selected_indexes_list:
            if model_index.isValid():
                model_index = model_index.sibling(model_index.row(), 0) #get the first column of the selected row, since it's the only one that contains data
                element = model_index.model().itemFromIndex(model_index)
                element.setCheckState(QtCore.Qt.Unchecked)


    def enableSelectedItems(self):
        selected_indexes_list = self.ui.layersShapesTreeView.selectedIndexes();

        for model_index in selected_indexes_list:
            if model_index.isValid():
                model_index = model_index.sibling(model_index.row(), 0) #get the first column of the selected row, since it's the only one that contains data
                element = model_index.model().itemFromIndex(model_index)
                element.setCheckState(QtCore.Qt.Checked)



    def doNotOptimizeRouteForSelectedItems(self):
        selected_indexes_list = self.ui.layersShapesTreeView.selectedIndexes();

        for model_index in selected_indexes_list:
            if model_index.isValid():
                model_index = model_index.sibling(model_index.row(), PATH_OPTIMISATION_COL) #get the first column of the selected row, since it's the only one that contains data
                element = model_index.model().itemFromIndex(model_index)
                if element.isCheckable():
                    element.setCheckState(QtCore.Qt.Unchecked)


    def optimizeRouteForSelectedItems(self):
        selected_indexes_list = self.ui.layersShapesTreeView.selectedIndexes();

        for model_index in selected_indexes_list:
            if model_index.isValid():
                model_index = model_index.sibling(model_index.row(), PATH_OPTIMISATION_COL) #get the first column of the selected row, since it's the only one that contains data
                element = model_index.model().itemFromIndex(model_index)
                if element.isCheckable():
                    element.setCheckState(QtCore.Qt.Checked)



    def actionOnKeyPress(self, key_code, item_index):
        """
        This function is a callback called from QTreeView class when a
        key is pressed on the treeView. If the key is the spacebar, O
        or T, then capture it to enable/disable shape, ...
        @param key_code: the key code as defined by QT
        @param item_index: the item on which the keyPress event occurred
        """
        result = False
        #Enable/disable checkbox
        if key_code == QtCore.Qt.Key_Space and item_index and item_index.isValid():
            item_index = item_index.sibling(item_index.row(), 0) #Get the first column of the row (ie the one that contains the enable/disable checkbox)
            item = item_index.model().itemFromIndex(item_index)
            item.setCheckState(QtCore.Qt.Unchecked if item.checkState() == QtCore.Qt.Checked else QtCore.Qt.Checked) #Toggle enable/disable checkbox
            #Ensure that the first col is the current index, so that we can still traverse the tree with the keyboard
            self.ui.layersShapesTreeView.setCurrentIndex(item_index)
            self.ui.entitiesTreeView.setCurrentIndex(item_index)
            result = True #Key handled

        #Optimize path checkbox
        if (key_code == QtCore.Qt.Key_O or key_code == QtCore.Qt.Key_T) and item_index and item_index.isValid():
            item_index = item_index.sibling(item_index.row(), PATH_OPTIMISATION_COL) #Get the column of the row that contains the "Optimize Path" checkbox
            item = item_index.model().itemFromIndex(item_index)
            if item.isCheckable():
                item.setCheckState(QtCore.Qt.Unchecked if item.checkState() == QtCore.Qt.Checked else QtCore.Qt.Checked) #Toggle checkbox
                #Ensure that the first col is the current index, so that we can still traverse the tree with the keyboard
                self.ui.layersShapesTreeView.setCurrentIndex(item_index)
                self.ui.entitiesTreeView.setCurrentIndex(item_index)
                result = True #Key handled

        return result



    def on_itemChanged(self, item):
        """
        This slot is called when some data changes in one of the
        TreeView. For us, since rows are read only, it is only
        triggered when a checkbox is checked/unchecked
        options
        @param item: item is the modified element. It can be a Shape, a Layer or an Entity
        """
        if item.column() == PATH_OPTIMISATION_COL:
            #User has clicked on the Path Optimisation (TSP) checkbox => update the corresponding data into the shape
            item_model_index = item.index().sibling(item.row(), 0) #get the first column of the selected row, since it's the only one that contains data
            first_col_item = item_model_index.model().itemFromIndex(item_model_index)
            if first_col_item and first_col_item.data(SHAPE_OBJECT).isValid():
                #Set tool path optimisation for the matching shape
                first_col_item.data(SHAPE_OBJECT).toPyObject().setToolPathOptimized(False if item.checkState() == QtCore.Qt.Unchecked else True)

        elif item.data(SHAPE_OBJECT).isValid() or item.data(CUSTOM_GCODE_OBJECT).isValid():
            self.updateCheckboxOfItem(item, item.checkState())
            if self.auto_update_export_order:
                #update export order and thus export drawing
                self.prepareExportOrderUpdate()

        elif item.data(LAYER_OBJECT).isValid():
            #Checkbox concerns a Layer object => check/uncheck each sub-items (shapes)
            self.traverseChildrenAndEnableDisable(self.layer_item_model, item.index(), item.checkState())
            if self.auto_update_export_order:
                self.prepareExportOrderUpdate()

        elif item.data(ENTITY_OBJECT).isValid():
            #Checkbox concerns an Entity object => check/uncheck each sub-items (shapes and/or other entities)
            self.traverseChildrenAndEnableDisable(self.entity_item_model, item.index(), item.checkState())
            if self.auto_update_export_order:
                self.prepareExportOrderUpdate()



    def updateCheckboxOfItem(self, item, check):
        """
        This function is used to effectively update the state of a
        checkbox and enable / disable texts when item is a shape
        @param item: item is the modified element. It can be a Shape, a Layer or an Entity
        @param check: the check state
        """
        item.model().blockSignals(True) #Avoid unnecessary signal loops (we don't want the treeView to emit itemChanged signal)
        item.setCheckState(check)
        item.model().blockSignals(False)

        if item.data(SHAPE_OBJECT).isValid():
            #Checkbox concerns a shape object
            real_item = item.data(SHAPE_OBJECT).toPyObject()
            real_item.setDisable(False if check == QtCore.Qt.Checked else True, True)

            #Update the other TreeViews
            item_index = self.findEntityItemIndexFromShape(real_item)
            if item_index:
                if item.model() == self.layer_item_model:
                    self.entity_item_model.blockSignals(True) #Avoid unnecessary signal loops (we don't want the treeView to emit itemChanged signal)
                    item_other_tree = self.entity_item_model.itemFromIndex(item_index)
                    item_other_tree.setCheckState(check)
                    self.enableDisableTreeRow(item_other_tree, check)
                    self.entity_item_model.blockSignals(False)
                self.traverseParentsAndUpdateEnableDisable(self.entity_item_model, item_index) #Update parents checkboxes

            item_index = self.findLayerItemIndexFromShape(real_item)
            if item_index:
                if item.model() == self.entity_item_model:
                    self.layer_item_model.blockSignals(True) #Avoid unnecessary signal loops (we don't want the treeView to emit itemChanged signal)
                    item_other_tree = self.layer_item_model.itemFromIndex(item_index)
                    item_other_tree.setCheckState(check)
                    self.enableDisableTreeRow(item_other_tree, check)
                    self.layer_item_model.blockSignals(False)
                self.traverseParentsAndUpdateEnableDisable(self.layer_item_model, item_index) #Update parents checkboxes

        if item.data(CUSTOM_GCODE_OBJECT).isValid():
            #Checkbox concerns a custom gcode object
            real_item = item.data(CUSTOM_GCODE_OBJECT).toPyObject()
            real_item.setDisable(False if check == QtCore.Qt.Checked else True)
            self.traverseParentsAndUpdateEnableDisable(self.layer_item_model, item.index()) #Update parents checkboxes

        self.enableDisableTreeRow(item, check)




    def enableDisableTreeRow(self, item, check):
        """
        Enable / disable all the columns from a row, except the first
        one (because the first column contains the checkbox that must
        stay enabled in order to be clickable)
        @param item: item is the modified element. It can be a Shape, a Layer or an Entity
        """
        current_tree_view = None
        if item.model() == self.layer_item_model:
            current_tree_view = self.ui.layersShapesTreeView
        else:
            current_tree_view = self.ui.entitiesTreeView

        item.model().blockSignals(True)
        i = 0
        row = 0
        if not item.parent():
            row_item = item.model().invisibleRootItem() #parent is 0, so we need to get the root item of the tree as parent
            i = item.columnCount()
        else:
            row_item = item.parent() #we are on one of the column of the row => take the parent, so that we get the complete row
            i = row_item.columnCount()
        row = item.row()
        while i > 1:
            i -= 1
            column_item = row_item.child(row, i)
            if column_item:
                column_item.setEnabled(False if check == QtCore.Qt.Unchecked else True)
                current_tree_view.update(column_item.index())
        item.model().blockSignals(False)

        #Update the display (refresh the treeView for the given item)
        current_tree_view.update(item.index())



    def removeCustomGCode(self):
        """
        Remove a custom GCode object from the treeView, just after the
        current item. Custom GCode are defined into the config.cfg file
        """
        logger.debug(_('Removing custom GCode...'))
        current_item_index = self.ui.layersShapesTreeView.currentIndex()

        if current_item_index and current_item_index.isValid():
            remove_row = current_item_index.row()

            item_model_index = current_item_index.sibling(remove_row, 0) #get the first column of the selected row, since it's the only one that contains data
            first_col_item = item_model_index.model().itemFromIndex(item_model_index)
            if first_col_item and first_col_item.data(CUSTOM_GCODE_OBJECT).isValid():
                #Item is a Custom GCode, so we can remove it
                real_item = first_col_item.data(CUSTOM_GCODE_OBJECT).toPyObject()
                real_item.LayerContent.shapes.remove(real_item)

                first_col_item.parent().removeRow(remove_row)

            else:
                logger.warning(_('Only Custom GCode items are removable!'))



    def addCustomGCodeAfter(self, action_name):
        """
        Add a custom GCode object into the treeView, just after the
        current item. Custom GCode are defined into the config.cfg file
        @param action_name: the name of the custom GCode to be inserted. This name must match one of the subsection names of [Custom_Actions] from the config file.
        """
        logger.debug(_('Adding custom GCode "%s"') %(action_name))

        g_code = "(No custom GCode defined)"
        if action_name and len(action_name) > 0:
            g_code = g.config.vars.Custom_Actions[str(action_name)].gcode

        current_item_index = self.ui.layersShapesTreeView.currentIndex()
        if current_item_index and current_item_index.isValid():
            push_row = current_item_index.row() + 1 #insert after the current row
            current_item = current_item_index.model().itemFromIndex(current_item_index)
            current_item_parent = current_item.parent()

            if not current_item_parent:
                #parent is 0, so we are probably on a layer
                #get the first column of the selected row, since it's the only one that contains data
                current_item_parent_index = current_item_index.sibling(current_item_index.row(), 0) 
                current_item_parent = current_item_parent_index.model().itemFromIndex(current_item_parent_index)
                push_row = 0 #insert before any shape

            if current_item_parent.data(LAYER_OBJECT).isValid():
                real_item_parent = current_item_parent.data(LAYER_OBJECT).toPyObject()

                #creates a new CustomGCode instance
                custom_gcode = CustomGCodeClass(action_name, len(real_item_parent.shapes), g_code, real_item_parent)

                #insert this new item at the end of the physical list
                real_item_parent.shapes.append(custom_gcode)

                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(":/images/pause.png"))
                item_col_0 = QtGui.QStandardItem(icon, "") #will only display a checkbox + an icon that will never be disabled
                item_col_0.setData(QtCore.QVariant(custom_gcode), CUSTOM_GCODE_OBJECT) #store a ref to the custom gcode in our treeView element
                item_col_0.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable)

                item_col_1 = QtGui.QStandardItem(custom_gcode.name)
                item_col_1.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

                item_col_2 = QtGui.QStandardItem(str(custom_gcode.nr))
                item_col_2.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled)

                item_col_3 = QtGui.QStandardItem()
                item_col_3.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled)

                #Deal with the checkboxes (shape enabled or disabled / send shape to TSP optimizer)
                item_col_0.setCheckState(QtCore.Qt.Checked)

                current_item_parent.insertRow(push_row, [item_col_0, item_col_1, item_col_2, item_col_3])
                self.ui.layersShapesTreeView.setCurrentIndex(current_item.index())


    def prepareExportOrderUpdate(self):
        """
        If the live update of export route is enabled, this function is
        called each time the shape order changes. It aims to update the drawing.
        """
        if self.auto_update_export_order:
            #Update the exported shapes
            self.updateExportOrder()

            #Emit the signal "exportOrderUpdated", so that the main can update tool path if he wants
            QtCore.QObject.emit(self, QtCore.SIGNAL("exportOrderUpdated"), self) #We only pass python objects as parameters => definition without parentheses (PyQt_PyObject)



    def setUpdateExportRoute(self, live_update):
        """
        Set or unset the live update of export route.
        """
        self.auto_update_export_order = live_update

        if live_update:
            #Live update the export route drawing
            QtCore.QObject.connect(self.ui.layersShapesTreeView, QtCore.SIGNAL("itemMoved"), self.prepareExportOrderUpdate)
            self.prepareExportOrderUpdate()

        else:
            #Don't automatically update the export route drawing
            QtCore.QObject.disconnect(self.ui.layersShapesTreeView, QtCore.SIGNAL("itemMoved"), self.prepareExportOrderUpdate)


