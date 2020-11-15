import React from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import {
  HashRouter as Router,
  Route,
  useLocation,
} from "react-router-dom";
import { StyleSheet, css } from "aphrodite";

import { COLWIDTH, BranchNode, LeafNode } from "./Common";
import { NavColumn } from "./NavColumn";
import { NavBreadcrumbs, InfoPane, Message } from "./CentrePane";

/**
 * Top level App component.
 */
const App = () => {
  return (
    <Router>
      <Route path="/"
        render={
          ({ location }) => {
            return <TestRunner url={location.pathname} />;
          }
        }
      />
    </Router>
  );
};

interface TestRunnerProps {
  url: string | null,
}

interface TestRunnerState {
  resultTree: BranchNode | null,
  loading: boolean,
  socket: SocketIOClient.Socket | null,
  errorMessage: string | null,
}

class TestRunner extends React.Component<TestRunnerProps, TestRunnerState> {
  constructor(props: TestRunnerProps) {
    super(props);
    this.state = {
      resultTree: null,
      loading: false,
      socket: null,
      errorMessage: null,
    }
    this.handleUpdate = this.handleUpdate.bind(this);
    this.handleTestRun = this.handleTestRun.bind(this);
    this.handleEnvToggle = this.handleEnvToggle.bind(this);
  }

  /**
   * When the component mounts, we initiate the websocket connection and
   * make an API call to get the result tree.
   */
  componentDidMount() {
    const socket = io();
    this.setState({ loading: true, socket: socket }, () => {
      socket.on('update', this.handleUpdate);
      this.getResultTree(10);
    });
  }

  /**
   * Make an API call to get the result tree data. Called at start of day when
   * this component mounts, then further updates are handled by the websocket
   * connection.
   */
  getResultTree(maxRetries: number) {
    axios.get("/api/v1/result-tree").then(response => {
      this.setState({ resultTree: response.data, loading: false });
    }).catch((reason: any) => {
      if (maxRetries === 0) {
        this.setState({ loading: false, errorMessage: String(reason) });
      } else {
        setTimeout(this.getResultTree, 100, maxRetries - 1)
      }
    });
  }

  /**
   * Handle an update event received over a websocket.
   * @param data Update data received over socket
   */
  handleUpdate(tree: BranchNode) {
    console.log("Handling websocket update");
    this.setState({ resultTree: tree });
  }

  /**
   * Run a test after its run button has been clicked.
   * @param short_id ID of node to run
   */
  handleTestRun(nodeid: string) {
    if (!this.state.socket) {
      console.log("Socket connection not yet established");
      return;
    }
    this.state.socket.emit("run test", nodeid);
  }

  /**
   * Run a test after its run button has been clicked.
   * @param short_id ID of node to run
   */
  handleEnvToggle(nodeid: string, start: boolean) {
    if (!this.state.socket) {
      console.log("Socket connection not yet established");
      return;
    }
    if (start) {
      this.state.socket.emit("start env", nodeid);
    } else {
      this.state.socket.emit("stop env", nodeid);
    }
  }

  /**
   * Render the test runner UI. Currently this component acts as the stateful
   * store and hands off rendering logic to a separate stateless component.
   */
  render() {
    const selection = parseSelection(this.props.url);

    if (this.state.loading) {
      return <MessageDisplay message="Loading..." selection={selection} />;
    }

    if (this.state.errorMessage) {
      return (
        <MessageDisplay
          message={this.state.errorMessage}
          selection={selection}
        />
      );
    }

    try {
      const { childBranches, childLeaves } = getCurrSelection(
        selection,
        this.state.resultTree,
      );

      return (
        <TestRunnerDisplay
          childBranches={childBranches}
          childLeaves={childLeaves}
          selection={selection}
          handleTestRun={this.handleTestRun}
          handleEnvToggle={this.handleEnvToggle}
        />
      );
    } catch (error) {
      if (error instanceof SelectionNotFound) {
        return <MessageDisplay message="404 Page Not Found" selection={selection} />;
      }
      throw error;
    }
  }
}

/**
 * Parse the current URL path (excluding query parameters) and return the
 * short_ids of the currently selected branches.
 * @param url URL path string
 */
const parseSelection = (url: string | null): Array<string> => {
  if (!url) {
    return [];
  }

  const trimmedPath = url.replace(/^\/+|\/+$/g, '');
  if (trimmedPath.length === 0) {
    return [];
  }
  const pathElements = trimmedPath.split("/");
  return pathElements.map(decodeURIComponent);
};

interface TestRunnerDisplayProps {
  childBranches: { [key: string]: BranchNode },
  childLeaves: { [key: string]: LeafNode },
  selection: Array<string>,
  handleTestRun: (short_id: string) => void,
  handleEnvToggle: (nodeid: string, start: boolean) => void,
}

/**
 * Render the navigation column, top breadcrumb menu and the central information
 * pane together.
 * @param props render properties
 */
const TestRunnerDisplay = (props: TestRunnerDisplayProps) => {
  const query = useQuery();
  const selectedLeafID = query.get("selectedLeaf");
  const selectedLeaf = selectedLeafID ? props.childLeaves[selectedLeafID] : null;

  return (
    <div>
      <NavColumn
        childBranches={props.childBranches}
        childLeaves={props.childLeaves}
        selectedLeafID={selectedLeafID}
        selection={props.selection}
        handleTestRun={props.handleTestRun}
        handleEnvToggle={props.handleEnvToggle}
      />
      <div className={css(styles.centrePane)}>
        <NavBreadcrumbs selection={props.selection} />
        <InfoPane selectedLeaf={selectedLeaf} />
      </div>
    </div>
  );
};

interface MessageDisplayProps {
  message: string,
  selection: Array<string>,
}

/**
 * Display a message.
 */
const MessageDisplay = (props: MessageDisplayProps) => (
  <div>
    <NavColumn
      childBranches={{}}
      childLeaves={{}}
      selectedLeafID={null}
      selection={[]}
      handleTestRun={(nodeid: string) => undefined}
      handleEnvToggle={(nodeid: string, start: boolean) => undefined}
    />
    <div className={css(styles.centrePane)}>
      <NavBreadcrumbs selection={props.selection} />
      <Message message={props.message} />
    </div>
  </div>
);

/**
 * Modified react hook to parse the current query parameters in the URL. These
 * are expected in the form "?x=y".
 */
const useQuery = () => new URLSearchParams(useLocation().search);

/**
 * Get the currently selected branch node, or null if the result tree is not yet
 * loaded.
 * @param state App state
 */
const getCurrSelection = (
  selection: Array<string>, resultTree: BranchNode | null
): {
  childBranches: { [key: string]: BranchNode },
  childLeaves: { [key: string]: LeafNode },
} => {
  if (!resultTree) {
    return { childBranches: {}, childLeaves: {} };
  }
  if (selection.length === 0) {
    return {
      childBranches: { [resultTree.short_id]: resultTree },
      childLeaves: {},
    };
  }

  const selectedBranch = selection.slice(1).reduce(
    (node: BranchNode | undefined, selection: string) => (
      node?.child_branches[selection]
    ),
    resultTree,
  );
  if (selectedBranch) {
    return {
      childBranches: selectedBranch.child_branches,
      childLeaves: selectedBranch.child_leaves
    };
  } else {
    throw new SelectionNotFound("Not found", selection);
  }
};

const styles = StyleSheet.create({
  centrePane: {
    "margin-left": COLWIDTH,
    padding: "10px 10px",
  },
});

class SelectionNotFound extends Error {
  public selection: Array<string>

  constructor(message: string, selection: Array<string>) {
    super(message);
    this.selection = selection;
  }
}

export default App;
