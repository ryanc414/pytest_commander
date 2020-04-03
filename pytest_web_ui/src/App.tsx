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
  useLocation,
} from "react-router-dom";
import { StyleSheet, css } from "aphrodite";

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

/**
 * Top level App component.
 */
const App = () => {
  return (
    <Router>
      <Switch>
        <Route path="/:selection"
          render={
            ({ match }) => <TestRunner
              selection={[decodeURIComponent(match.params.selection)]}
              url={match.url}
            />
          }
        />
        <Route path="/">
          <TestRunner selection={[]} url="" />
        </Route>
      </Switch>
    </Router>
  );
};

interface AppProps {
  selection: Array<string>,
  url: string,
}

interface AppState {
  resultTree: BranchNode | null,
  loading: boolean,
  socket: SocketIOClient.Socket | null,
}

class TestRunner extends React.Component<AppProps, AppState> {
  constructor(props: AppProps) {
    super(props);
    this.state = {
      resultTree: null,
      loading: false,
      socket: null,
    }
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

  /**
   * Handle an update event received over a websocket.
   * @param data Update data received over socket
   */
  handleUpdate(data: UpdateData) {

    const root = this.state.resultTree;
    if (!root) {
      return;
    }

    this.setState((state) => {
      const newTree = updateResultTree(
        root, data.node.parent_nodeids, data,
      );
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

  render() {
    const selectedBranch = getSelectedBranch(
      this.props.selection,
      this.state.resultTree,
    );

    return (
      <Switch>
        <Route
          path={`${this.props.url}/:selection`}
          render={
            ({ match }) => <TestRunner
              selection={
                this.props.selection.concat(
                  [decodeURIComponent(match.params.selection)]
                )
              }
              url={match.url}
            />
          }
        />
        <Route path={this.props.url}>
          <TestRunnerDisplay
            selectedBranch={selectedBranch}
            selection={this.props.selection}
            handleTestRun={this.handleTestRun}
          />
        </Route>
      </Switch>
    );
  }
}

interface TestRunnerDisplayProps {
  selectedBranch: BranchNode | null,
  selection: Array<string>,
  handleTestRun: (nodeid: string) => void,
}

/**
 * Render the navigation column, top breadcrumb menu and the central information
 * pane together.
 * @param props render properties
 */
const TestRunnerDisplay = (props: TestRunnerDisplayProps) => {
  const query = useQuery();
  const selectedLeafID = query.get("selectedLeaf");
  const selectedLeaf = (selectedLeafID && props.selectedBranch) ?
    props.selectedBranch.child_leaves[selectedLeafID] : null;

  return (
    <Sidebar
      sidebar={
        <NavColumn
          selectedBranch={props.selectedBranch}
          selectedLeafID={selectedLeafID}
          selection={props.selection}
          handleTestRun={props.handleTestRun}
        />
      }
      open={true}
      docked={true}
      styles={{
        sidebar: {
          background: "white",
          transition: "none",
          webkitTransition: "none",
        }
      }}
    >
      <NavBreadcrumbs selection={props.selection} />
      <InfoPane selectedLeaf={selectedLeaf} />
    </Sidebar >
  );
};

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
    return ret;
  }

  if (updateData.is_leaf) {
    const childLeaves = { ...currNode.child_leaves };
    childLeaves[updateData.node.nodeid] = (updateData.node as LeafNode);
    const ret = {
      ...currNode,
      child_leaves: childLeaves,
    };
    return ret;
  } else {
    const childBranches = { ...currNode.child_branches };
    childBranches[updateData.node.nodeid] = (updateData.node as BranchNode);
    const ret = {
      ...currNode,
      child_branches: childBranches,
    };
    return ret;
  }
}

/**
 * Get the currently selected branch node, or null if the result tree is not yet
 * loaded.
 * @param state App state
 */
const getSelectedBranch = (
  selection: Array<string>, resultTree: BranchNode | null
) => {
  if (resultTree) {
    const selectedBranch = selection.reduce(
      (node: BranchNode | undefined, selection: string) => (
        node?.child_branches[selection]
      ),
      resultTree,
    );
    if (selectedBranch) {
      return selectedBranch;
    } else {
      console.log(selection);
      return null;
    }
  } else {
    return null;
  }
};

interface NavColumnProps {
  selectedBranch: BranchNode | null,
  selectedLeafID: string | null,
  selection: Array<string>,
  handleTestRun: (nodeid: string) => void,
}

/**
 * NavColumn component: renders the current navigation selection.
 * @param props Component props
 */
const NavColumn = (props: NavColumnProps) => {
  if (!props.selectedBranch) {
    return <span>Loading...</span>;
  }

  const childBranches = Object.keys(props.selectedBranch.child_branches);
  const childLeaves = Object.keys(props.selectedBranch.child_leaves);

  return (
    <ListGroup className={css(styles.navColumn)}>
      <NavBranchEntries
        childBranches={childBranches}
        selection={props.selection}
        handleTestRun={props.handleTestRun}
      />
      <NavLeafEntries
        childLeaves={childLeaves}
        handleTestRun={props.handleTestRun}
        selectedLeafID={props.selectedLeafID}
      />
    </ListGroup>
  );
};

interface NavBranchEntriesProps {
  childBranches: Array<string>,
  selection: Array<string>,
  handleTestRun: (nodeid: string) => void,
}

/**
 * Render entries in the nav column for branch nodes that are children of the
 * currently selected node.
 * @param props Render props
 */
const NavBranchEntries = (props: NavBranchEntriesProps) => (
  <>
    {
      props.childBranches.map(
        (nodeid: string) => (
          <ListGroupItem key={nodeid}>
            <span className={css(styles.navLabel)}>
              <Link
                to={
                  props.selection
                    .concat([nodeid])
                    .map(encodeURIComponent)
                    .join("/")
                }
              >
                {nodeid}
              </Link>
            </span>
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
  </>
);

interface NavLeafEntriesProps {
  childLeaves: Array<string>,
  selectedLeafID: string | null,
  handleTestRun: (nodeid: string) => void,
}

/**
 * Render entries in the navigation column for child leaves of the currently
 * selected node.
 * @param props Render props
 */
const NavLeafEntries = (props: NavLeafEntriesProps) => (
  <>
    {
      props.childLeaves.map(
        (nodeid: string) => {
          const label = (nodeid === props.selectedLeafID) ?
            nodeid :
            (
              <Link
                to={`?selectedLeaf=${encodeURIComponent(nodeid)}`}
              >
                {nodeid}
              </Link>
            );

          return (
            <ListGroupItem key={nodeid}>
              <span className={css(styles.navLabel)}>{label}</span>
              <FontAwesomeIcon
                icon={faPlay}
                onClick={(e: React.MouseEvent) => {
                  e.stopPropagation();
                  props.handleTestRun(nodeid);
                }}
              />
            </ListGroupItem>
          );
        }
      )
    }
  </>
);

interface InfoPaneProps {
  selectedLeaf: LeafNode | null,
}

/**
 * InfoPane component: renders information on the currently selected testcase
 * (if any)
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
  selection: Array<string>
}

const NavBreadcrumbs = (props: NavBreadcrumbsProps) => {
  const numSelected = props.selection.length;

  if (!numSelected) {
    return (
      <Breadcrumb>
        <BreadcrumbItem key="home">
          <FontAwesomeIcon icon={faHome} />
        </BreadcrumbItem>
      </Breadcrumb>
    );
  }

  const currSelected = props.selection[numSelected - 1];
  const restSelected = props.selection.slice(0, numSelected - 1);

  return (
    <Breadcrumb>
      <BreadcrumbItem key="home">
        <Link to="/">
          <FontAwesomeIcon icon={faHome} />
        </Link>
      </BreadcrumbItem>
      {
        restSelected.map(
          (nodeid: string, index: number) => (
            <BreadcrumbItem key={nodeid}>
              <Link
                to={
                  "/" +
                  props.selection
                    .slice(0, index + 1)
                    .map(encodeURIComponent)
                    .join("/")
                }
              >
                {nodeid}
              </Link>
            </BreadcrumbItem>
          )
        )
      }
      <BreadcrumbItem>{currSelected}</BreadcrumbItem>
    </Breadcrumb>
  );
};

const useQuery = () => new URLSearchParams(useLocation().search);

const styles = StyleSheet.create({
  navColumn: { width: "25em" },
  navLabel: {
    display: "inline-block",
    "text-overflow": "ellipsis",
    "white-space": "nowrap",
    fontSize: "small",
    width: "95%",
  }
});

export default App;
