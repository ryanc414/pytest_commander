import React from 'react';
import axios from 'axios';
import {
  ListGroup, ListGroupItem, Breadcrumb, BreadcrumbItem
} from 'reactstrap';
import Sidebar from 'react-sidebar';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome, faPlay } from '@fortawesome/free-solid-svg-icons';
import io from 'socket.io-client';
import {
  HashRouter as Router,
  Switch,
  Route,
  Link,
  useParams,
  useHistory,
} from "react-router-dom";


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
  selectedLeaf: string | null,
  socket: SocketIOClient.Socket | null,
}

/**
 * Top level App component.
 */
const App = () => {
  return (
    <Router>
      <Switch>
        <Route path="/:selection" children={<TestRunner />} />
      </Switch>
    </Router>
  );
};


class TestRunner extends React.Component<object, AppState> {
  constructor(props: object) {
    super(props);
    this.state = {
      resultTree: null,
      loading: false,
      sidebarOpen: true,
      selectedLeaf: null,
      socket: null,
    }
    this.onSetSidebarOpen = this.onSetSidebarOpen.bind(this);
    this.handleLeafClick = this.handleLeafClick.bind(this);
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
    console.log(data);

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
   * Handle a leaf node being clicked.
   * @param nodeid ID of clicked leaf node
   */
  handleLeafClick(nodeid: string) {
    this.setState((state) => ({
      selectedLeaf: nodeid,
    }))
  }

  render() {
    const { selection } = useParams();
    const selectedBranch = getSelectedBranch(selection, this.state.resultTree);

    const selectedLeaf = selectedBranch && this.state.selectedLeaf ?
      selectedBranch.child_leaves[this.state.selectedLeaf] : null;

    return (
      <Sidebar
        sidebar={
          <NavColumn
            selectedBranch={selectedBranch}
            selection={selection}
            handleLeafClick={this.handleLeafClick}
            handleTestRun={this.handleTestRun}
          />
        }
        open={this.state.sidebarOpen}
        docked={true}
        onSetOpen={this.onSetSidebarOpen}
        styles={{ sidebar: { background: "white" } }}
      >
        <NavBreadcrumbs selection={selection} />
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

    const childBranches = { ...currNode.child_branches };
    childBranches[head] = updateResultTree(
      currNode.child_branches[head], tail, updateData
    );
    const ret = {
      ...currNode,
      child_branches: childBranches,
    };
    console.log(ret);
    return ret;
  }

  console.log(updateData);

  if (updateData.is_leaf) {
    console.log(currNode);
    const childLeaves = { ...currNode.child_leaves };
    childLeaves[updateData.node.nodeid] = (updateData.node as LeafNode);
    const ret = {
      ...currNode,
      child_leaves: childLeaves,
    };
    console.log(ret);
    return ret;
  } else {
    const childBranches = { ...currNode.child_branches };
    childBranches[updateData.node.nodeid] = (updateData.node as BranchNode);
    const ret = {
      ...currNode,
      child_branches: childBranches,
    };
    console.log(ret);
    return ret;
  }
}

/**
 * Get the currently selected branch node, or null if the result tree is not yet loaded.
 * @param state App state
 */
const getSelectedBranch = (
  selection: string | undefined, resultTree: BranchNode | null
) => {
  if (resultTree) {
    if (selection) {
      return selection.split("/").reduce(
        (node: BranchNode, selection: string) => node.child_branches[selection],
        resultTree,
      );
    } else {
      return resultTree;
    }
  } else {
    return null;
  }
};

interface NavProps {
  selectedBranch: BranchNode | null,
  selection: string | undefined,
  handleLeafClick: (nodeid: string) => void,
  handleTestRun: (nodeid: string) => void,
}

/**
 * NavColumn component: renders the current navigation selection.
 * @param props Component props
 */
const NavColumn = (props: NavProps) => {
  const history = useHistory();

  if (!props.selectedBranch) {
    return <span>Loading...</span>;
  }

  const childBranches = Object.keys(props.selectedBranch.child_branches);
  const childLeaves = Object.keys(props.selectedBranch.child_leaves);
  const selection = props.selection ? props.selection : "";

  return (
    <ListGroup>
      {
        childBranches.map(
          (nodeid: string) => (
            <ListGroupItem onClick={
              () => history.push(selection + "/" + nodeid)
            }>
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
  selection: string | undefined
}

const NavBreadcrumbs = (props: NavBreadcrumbsProps) => {
  const selection = props.selection ? props.selection.split("/") : [];
  const numSelected = selection.length;
  const history = useHistory();

  if (!numSelected) {
    return (
      <Breadcrumb>
        <BreadcrumbItem><FontAwesomeIcon icon={faHome} /></BreadcrumbItem>
      </Breadcrumb>
    );
  }

  const currSelected = selection[numSelected - 1];
  const restSelected = selection.slice(0, numSelected - 1);

  return (
    <Breadcrumb>
      <BreadcrumbItem>
        <FontAwesomeIcon
          icon={faHome}
          onClick={() => history.push("/")}
        />
      </BreadcrumbItem>
      {
        restSelected.map(
          (nodeid: string, index: number) => (
            <BreadcrumbItem>
              <Link to={"/" + selection.slice(0, index).join("/")} />
            </BreadcrumbItem>
          )
        )
      }
      <BreadcrumbItem>{currSelected}</BreadcrumbItem>
    </Breadcrumb>
  );
};

export default App;
