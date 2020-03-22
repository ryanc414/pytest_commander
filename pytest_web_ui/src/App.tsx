import React from 'react';
import axios from 'axios';
import {
  ListGroup, ListGroupItem, Breadcrumb, BreadcrumbItem
} from 'reactstrap';
import Sidebar from 'react-sidebar';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome, faPlay } from '@fortawesome/free-solid-svg-icons';
import io from 'socket.io-client';

interface BranchNode {
  nodeid: string,
  status: string,
  parent_nodeids: Array<string>,
  child_branches: { [key: string]: BranchNode },
  child_leaves: { [key: string]: LeafNode },
}

interface LeafNode {
  nodeid: string,
  status: string,
  parent_nodeids: Array<string>,
  longrepr: string,
}

interface UpdateData {
  node: LeafNode | BranchNode,
  is_leaf: boolean,
}

interface AppState {
  resultTree: BranchNode | null,
  loading: boolean,
  sidebarOpen: boolean,
  selectedBranches: Array<string>,
  selectedLeaf: string | null,
  socket: SocketIOClient.Socket | null,
}

/**
 * Top level App component.
 */
class App extends React.Component<object, AppState> {
  constructor(props: object) {
    super(props);
    this.state = {
      resultTree: null,
      loading: false,
      sidebarOpen: true,
      selectedBranches: [],
      selectedLeaf: null,
      socket: null,
    }
    this.onSetSidebarOpen = this.onSetSidebarOpen.bind(this);
    this.handleBranchClick = this.handleBranchClick.bind(this);
    this.handleLeafClick = this.handleLeafClick.bind(this);
    this.handleBreadcrumbClick = this.handleBreadcrumbClick.bind(this);
    this.handleUpdate = this.handleUpdate.bind(this);
    this.handleTestRun = this.handleTestRun.bind(this);
  }

  componentDidMount() {
    const socket = io();
    this.setState({ loading: true, socket: socket }, () => {
      socket.on('update', this.handleUpdate);
      this.getResultTree();
    });
  }

  getResultTree() {
    axios.get("/api/v1/result-tree").then(response => {
      this.setState({ resultTree: response.data, loading: false });
    });
  }

  onSetSidebarOpen(open: boolean) {
    this.setState({ sidebarOpen: open })
  }

  /**
   * Handle an update event received over a websocket.
   * @param data Update data received over socket
   */
  handleUpdate(data: UpdateData) {
    console.log("Received update: " + data);

    const root = this.state.resultTree;
    if (!root) {
      console.log("Received update before result tree is loaded, ignoring.");
      return;
    }

    this.setState((state) => {
      const newTree = updateResultTree(
        root, data.node.parent_nodeids, data,
      );
      console.log(newTree);
      return { resultTree: newTree };
    });
  }

  /**
   * Run a test after its run button has been clicked.
   * @param nodeid ID of node to run
   */
  handleTestRun(nodeid: string) {
    if (!this.state.socket) {
      console.log("Socket connection not yet established");
      return;
    }
    this.state.socket.emit("run test", nodeid);
  }

  /**
   * Handle a branch node being clicked.
   * @param nodeid ID of clicked branch node
   */
  handleBranchClick(nodeid: string) {
    this.setState((state) => ({
      selectedBranches: state.selectedBranches.concat([nodeid]),
      selectedLeaf: null,
    }));
  }

  /**
   * Handle a leaf node being clicked.
   * @param nodeid ID of clicked leaf node
   */
  handleLeafClick(nodeid: string) {
    this.setState((state) => ({
      selectedLeaf: nodeid,
    }))
  }

  handleBreadcrumbClick(nodeid: string, index: number) {
    this.setState((state: AppState) => {
      // An index of -1 is used to indicate the home icon was clicked.
      if (index < 0) {
        return { selectedBranches: [] };
      }

      if (state.selectedBranches[index] !== nodeid) {
        console.log(
          "Breadcrumb entry " + nodeid + " not in current selection."
        );
        return null;
      }

      return {
        selectedBranches: state.selectedBranches.slice(0, index + 1)
      };
    });
  }

  render() {
    const selectedBranch = getSelectedBranch(this.state);

    const selectedLeaf = selectedBranch && this.state.selectedLeaf ?
      selectedBranch.child_leaves[this.state.selectedLeaf] : null;

    return (
      <Sidebar
        sidebar={
          < NavColumn
            selectedBranch={selectedBranch}
            handleBranchClick={this.handleBranchClick}
            handleLeafClick={this.handleLeafClick}
            handleTestRun={this.handleTestRun}
          />
        }
        open={this.state.sidebarOpen}
        docked={true}
        onSetOpen={this.onSetSidebarOpen}
        styles={{ sidebar: { background: "white" } }}
      >
        <NavBreadcrumbs
          selectedBranches={this.state.selectedBranches}
          handleBreadcrumbClick={this.handleBreadcrumbClick}
        />
        <InfoPane selectedLeaf={selectedLeaf} />
      </Sidebar >
    );
  }
}

/**
 * Update a particular node in the result tree with new data.
 * @param currNode Existing in result tree to update
 * @param parentNodeIds List of parent node IDs to reach node to update
 * @param updateData Update data for new node
 */
const updateResultTree = (
  currNode: BranchNode, parentNodeIds: Array<string>, updateData: UpdateData
): BranchNode => {
  if (parentNodeIds.length > 0) {
    const head = parentNodeIds[0];
    const tail = parentNodeIds.slice(1, parentNodeIds.length);
    return {
      ...currNode,
      child_branches: {
        ...currNode.child_branches,
        head: updateResultTree(currNode.child_branches[head], tail, updateData),
      }
    };
  }

  if (updateData.is_leaf) {
    const childLeaves = { ...currNode.child_leaves };
    childLeaves[updateData.node.nodeid] = (updateData.node as LeafNode);
    return {
      ...currNode,
      child_leaves: childLeaves,
    }
  } else {
    const childBranches = { ...currNode.child_branches };
    childBranches[updateData.node.nodeid] = (updateData.node as BranchNode);
    return {
      ...currNode,
      child_branches: childBranches,
    }
  }
}

/**
 * Get the currently selected branch node, or null if the result tree is not yet loaded.
 * @param state App state
 */
const getSelectedBranch = (state: AppState) => {
  if (state.resultTree) {
    return state.selectedBranches.reduce(
      (node: BranchNode, selection: string) => node.child_branches[selection],
      state.resultTree,
    );
  } else {
    return null;
  }
};

interface NavProps {
  selectedBranch: BranchNode | null,
  handleBranchClick: (nodeid: string) => void,
  handleLeafClick: (nodeid: string) => void,
  handleTestRun: (nodeid: string) => void,
}

/**
 * NavColumn component: renders the current navigation selection.
 * @param props Component props
 */
const NavColumn = (props: NavProps) => {
  if (!props.selectedBranch) {
    return <span>Loading...</span>;
  }

  const childBranches = Object.keys(props.selectedBranch.child_branches);
  const childLeaves = Object.keys(props.selectedBranch.child_leaves);
  return (
    <ListGroup>
      {
        childBranches.map(
          (nodeid: string) => (
            <ListGroupItem onClick={(e: React.MouseEvent) => props.handleBranchClick(nodeid)}>
              {nodeid}
              <FontAwesomeIcon
                icon={faPlay}
                onClick={(e: React.MouseEvent) => {
                  e.stopPropagation();
                  props.handleTestRun(nodeid);
                }}
              />
            </ListGroupItem>
          )
        )
      }
      {
        childLeaves.map(
          (nodeid: string) => (
            <ListGroupItem onClick={() => props.handleLeafClick(nodeid)}>
              {nodeid}
              <FontAwesomeIcon
                icon={faPlay}
                onClick={(e: React.MouseEvent) => {
                  e.stopPropagation();
                  props.handleTestRun(nodeid);
                }}
              />
            </ListGroupItem>
          )
        )
      }
    </ListGroup>
  );
}

interface InfoPaneProps {
  selectedLeaf: LeafNode | null,
}

/**
 * InfoPane component: renders information on the currently selected testcase (if any)
 * @param props Component props
 */
const InfoPane = (props: InfoPaneProps) => {
  if (!props.selectedLeaf) {
    return <div>Please select a test.</div>
  }

  return (
    <>
      <div>{"nodeid: " + props.selectedLeaf.nodeid}</div>
      <div>{"status: " + props.selectedLeaf.status}</div>
      <div>{"longrepr: " + props.selectedLeaf.longrepr}</div>
    </>
  )
}

interface NavBreadcrumbsProps {
  selectedBranches: Array<string>,
  handleBreadcrumbClick: (nodeid: string, index: number) => void,
}

const NavBreadcrumbs = (props: NavBreadcrumbsProps) => {
  const numSelected = props.selectedBranches.length;

  if (!numSelected) {
    return (
      <Breadcrumb>
        <BreadcrumbItem><FontAwesomeIcon icon={faHome} /></BreadcrumbItem>
      </Breadcrumb>
    );
  }

  const currSelected = props.selectedBranches[numSelected - 1];
  const restSelected = props.selectedBranches.slice(0, numSelected - 1);

  return (
    <Breadcrumb>
      <BreadcrumbItem>
        <FontAwesomeIcon
          icon={faHome}
          onClick={() => props.handleBreadcrumbClick("", -1)}
        />
      </BreadcrumbItem>
      {
        restSelected.map(
          (nodeid: string, index: number) => (
            <BreadcrumbItem>
              <button onClick={() => props.handleBreadcrumbClick(nodeid, index)}>
                {nodeid}
              </button>
            </BreadcrumbItem>
          )
        )
      }
      <BreadcrumbItem>{currSelected}</BreadcrumbItem>
    </Breadcrumb>
  );
};

export default App;
